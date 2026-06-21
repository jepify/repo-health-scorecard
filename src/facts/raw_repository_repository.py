from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Self

from pydantic import BaseModel

from src.models.models import GitHubRepository


class FileMatch(BaseModel):
    """A single line matching a search pattern (grep-like)."""

    path: Path
    line_number: int
    line: str


class SearchResult(BaseModel):
    """All matches for a search pattern."""

    pattern: str
    matches: list[FileMatch]


class FileListResult(BaseModel):
    """All files matching a glob (find-like)."""

    glob: str
    paths: list[Path]


class RawCodeRepository:
    """Shallow-clones a GitHub repository's ``HEAD`` and queries its files.

    See ADR 003. Use as a context manager, or call :meth:`setup` and
    :meth:`teardown` explicitly to manage the temporary checkout.
    """

    def __init__(self, repository: GitHubRepository) -> None:
        self._repository = repository
        self._checkout_dir: Path | None = None

    @property
    def checkout_dir(self) -> Path:
        if self._checkout_dir is None:
            raise RuntimeError("Repository is not set up. Call setup() first.")
        return self._checkout_dir

    def setup(self) -> Self:
        """Create a temp folder and shallow-clone ``HEAD`` into it."""
        if self._checkout_dir is not None:
            return self

        checkout_dir = Path(tempfile.mkdtemp(prefix="repo-health-"))
        try:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--single-branch",
                    self._repository.clone_url,
                    str(checkout_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
        except BaseException:
            shutil.rmtree(checkout_dir, ignore_errors=True)
            raise

        self._checkout_dir = checkout_dir
        return self

    def teardown(self) -> None:
        """Remove the temporary checkout, if any."""
        if self._checkout_dir is not None:
            shutil.rmtree(self._checkout_dir, ignore_errors=True)
            self._checkout_dir = None

    def __enter__(self) -> Self:
        return self.setup()

    def __exit__(self, *_: object) -> None:
        self.teardown()

    def search(self, pattern: str) -> SearchResult:
        """Find lines matching ``pattern`` across files (grep-like)."""
        # No binary files, with line numbers, no color codes, and ignore .git/
        result = subprocess.run(
            ["git", "grep", "--no-color", "-n", "-I", "-e", pattern],
            cwd=self.checkout_dir,
            capture_output=True,
            text=True,
        )
        matches: list[FileMatch] = []
        for raw_line in result.stdout.splitlines():
            path_part, _, rest = raw_line.partition(":")
            line_part, _, content = rest.partition(":")
            if not line_part.isdigit():
                continue
            matches.append(
                FileMatch(
                    path=Path(path_part),
                    line_number=int(line_part),
                    line=content,
                )
            )
        return SearchResult(pattern=pattern, matches=matches)

    def list_files(self, glob: str = "*") -> FileListResult:
        """Find files matching ``glob`` (find-like)."""
        root = self.checkout_dir
        paths = sorted(p.relative_to(root) for p in root.glob(glob) if p.is_file() and ".git" not in p.parts)
        return FileListResult(glob=glob, paths=paths)
