import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, NoReturn, Protocol, override

_API_BASE_URL = "https://api.github.com"
_API_VERSION = "2022-11-28"
_USER_AGENT = "repo-health-scorecard"

# Statistics endpoints return 202 while GitHub computes them in the background.
_STATS_MAX_ATTEMPTS = 5
_STATS_RETRY_SECONDS = 2.0


class GitHubApiException(Exception):
    """A GitHub REST API request failed."""


class GitHubRateLimitException(GitHubApiException):
    """The GitHub REST API rate limit has been exhausted.

    Carries the time the limit resets so callers can surface an actionable
    message instead of a generic failure. Authenticating with a token raises the
    hourly limit from 60 (unauthenticated) to 5000 requests.
    """

    def __init__(self, reset_at: datetime | None) -> None:
        self.reset_at = reset_at
        suffix = f" Resets at {reset_at.isoformat()}." if reset_at is not None else ""
        super().__init__("GitHub API rate limit exceeded. Set GITHUB_TOKEN to raise the limit from 60 to 5000 requests/hour." + suffix)


class GitHubAPIClient(Protocol):
    """Performs GET requests against the GitHub REST API.

    Injected into REST-backed facts repositories so they can be tested without
    real network access (see ADR 001). Returns the decoded JSON body; callers
    parse it into typed models at their boundary.
    """

    def get_collection(self, path: str, params: dict[str, str] | None = None) -> list[Any]: ...

    def get_computed_collection(self, path: str, params: dict[str, str] | None = None) -> list[Any]: ...


class DefaultGitHubAPIClient(GitHubAPIClient):
    """Default :class:`GitHubAPIClient` backed by :mod:`urllib`.

    Follows ``Link`` header pagination to collect every page of a list endpoint,
    authenticates with ``GITHUB_TOKEN`` when present, and turns rate-limit
    responses into a :class:`GitHubRateLimitException`.
    """

    def __init__(self, token: str | None = None, base_url: str = _API_BASE_URL) -> None:
        self._token = token or os.environ.get("GITHUB_TOKEN")
        self._base_url = base_url

    @override
    def get_collection(self, path: str, params: dict[str, str] | None = None) -> list[Any]:
        """GET every page of a list endpoint and return the concatenated items."""

        url: str | None = self._build_url(path, params)

        items: list[Any] = []
        while url is not None:
            _status, page, url = self._get_page(url)
            if not isinstance(page, list):
                raise GitHubApiException(f"Expected a JSON array from {path!r}, got {type(page).__name__}")
            items.extend(page)
        return items

    @override
    def get_computed_collection(self, path: str, params: dict[str, str] | None = None) -> list[Any]:
        """GET a statistics endpoint, retrying while GitHub computes it (HTTP 202).

        Statistics are generated in the background; the first request often
        returns 202 with an empty body. Retries a bounded number of times before
        giving up rather than blocking indefinitely.
        """

        url = self._build_url(path, params)
        for attempt in range(_STATS_MAX_ATTEMPTS):
            status, body, _next = self._get_page(url)
            if status == 202:
                if attempt < _STATS_MAX_ATTEMPTS - 1:
                    time.sleep(_STATS_RETRY_SECONDS)
                continue
            if not isinstance(body, list):
                raise GitHubApiException(f"Expected a JSON array from {path!r}, got {type(body).__name__}")
            return body
        raise GitHubApiException(f"GitHub is still computing statistics for {path!r}; try again shortly.")

    def _build_url(self, path: str, params: dict[str, str] | None) -> str:
        url = f"{self._base_url}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        return url

    def _get_page(self, url: str) -> tuple[int, Any, str | None]:
        request = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(request) as response:  # noqa: S310 - https URL built from a validated base
                status = response.status
                raw = response.read().decode("utf-8")
                next_url = self._parse_next_link(response.headers.get("Link"))
        except urllib.error.HTTPError as error:
            self._raise_for_error(error)
        except urllib.error.URLError as error:
            raise GitHubApiException(f"GitHub API request to {url} failed: {error.reason}") from error

        body = json.loads(raw) if raw else []
        return status, body, next_url

    def _raise_for_error(self, error: urllib.error.HTTPError) -> NoReturn:
        if error.code in (403, 429) and error.headers.get("X-RateLimit-Remaining") == "0":
            raise GitHubRateLimitException(self._parse_reset(error.headers.get("X-RateLimit-Reset"))) from error
        raise GitHubApiException(f"GitHub API request failed with status {error.code}: {error.reason}") from error

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": _USER_AGENT,
            "X-GitHub-Api-Version": _API_VERSION,
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    @staticmethod
    def _parse_reset(reset_header: str | None) -> datetime | None:
        if not reset_header:
            return None
        try:
            return datetime.fromtimestamp(int(reset_header))
        except ValueError:
            return None

    @staticmethod
    def _parse_next_link(link_header: str | None) -> str | None:
        """Extract the ``rel="next"`` URL from a GitHub ``Link`` header, if any."""

        if not link_header:
            return None
        for part in link_header.split(","):
            segments = part.split(";")
            if len(segments) < 2:
                continue
            url = segments[0].strip().strip("<>")
            relation = segments[1].strip()
            if relation == 'rel="next"':
                return url
        return None
