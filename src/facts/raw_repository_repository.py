import re
import shutil
import tempfile
from pathlib import Path
from typing import Self

from pydantic import BaseModel

from src.facts.repository_cloner import RepositoryCloner, ShallowGitRepositoryCloner
from src.facts.subprocess_runner import DefaultSubprocessRunner, SubprocessRunner
from src.models.github import GitHubRepository


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

    def __init__(
        self,
        repository: GitHubRepository,
        dep_cloner: RepositoryCloner | None = None,
        dep_subprocess_runner: SubprocessRunner | None = None,
    ) -> None:
        self._repository = repository
        # Cloning is the side-effectful step; inject a fake to test on plain files.
        self._cloner = dep_cloner or ShallowGitRepositoryCloner()
        self._subprocess_runner = dep_subprocess_runner or DefaultSubprocessRunner()
        self._checkout_dir: Path | None = None
        self._commit_sha: str | None = None

    @property
    def checkout_dir(self) -> Path:
        if self._checkout_dir is None:
            raise RuntimeError("Repository is not set up. Call setup() first.")
        return self._checkout_dir

    @property
    def commit_sha(self) -> str:
        """The full SHA of the cloned ``HEAD`` commit."""
        if self._commit_sha is None:
            raise RuntimeError("Repository is not set up. Call setup() first.")
        return self._commit_sha

    def setup(self) -> Self:
        """Create a temp folder and shallow-clone ``HEAD`` into it."""
        if self._checkout_dir is not None:
            return self

        print("Setting up repository:", self._repository.clone_url)

        checkout_dir = Path(tempfile.mkdtemp(prefix="repo-health-"))
        print("Created temporary checkout directory:", checkout_dir)
        try:
            self._cloner.clone(self._repository, checkout_dir)
            commit_sha = self._subprocess_runner.run(
                ["git", "rev-parse", "HEAD"],
                cwd=checkout_dir,
                check=True,
            ).stdout.strip()
        except BaseException:
            shutil.rmtree(checkout_dir, ignore_errors=True)
            raise

        self._checkout_dir = checkout_dir
        self._commit_sha = commit_sha
        return self

    def teardown(self) -> None:
        """Remove the temporary checkout, if any."""
        if self._checkout_dir is not None:
            print("Tearing down repository, removing checkout directory:", self._checkout_dir)
            shutil.rmtree(self._checkout_dir, ignore_errors=True)
            self._checkout_dir = None
            self._commit_sha = None

    def __enter__(self) -> Self:
        return self.setup()

    def __exit__(self, *_) -> None:
        self.teardown()

    def search(self, pattern: str) -> SearchResult:
        """Find lines matching ``pattern`` across files (grep-like)."""
        regex = re.compile(pattern)
        root = self.checkout_dir
        matches: list[FileMatch] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file() or ".git" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError, OSError:
                continue  # skip binary / unreadable files
            for line_number, line in enumerate(text.splitlines(), start=1):
                if regex.search(line):
                    matches.append(
                        FileMatch(
                            path=path.relative_to(root),
                            line_number=line_number,
                            line=line,
                        )
                    )
        return SearchResult(pattern=pattern, matches=matches)

    def list_files(self, glob: str = "*") -> FileListResult:
        """Find files matching ``glob`` (find-like), recursing into subdirectories."""
        # fd recurses by default; --hidden keeps dotfiles (e.g. .github/), and we
        # exclude .git so the checkout's own metadata never leaks into results.
        result = self._subprocess_runner.run(
            ["fd", "--hidden", "-i", "--exclude", ".git", "--type", "f", "--glob", glob],
            cwd=self.checkout_dir,
        )
        paths = sorted(Path(line) for line in result.stdout.splitlines() if line)
        return FileListResult(glob=glob, paths=paths)
