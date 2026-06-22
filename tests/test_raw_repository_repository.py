from collections.abc import Sequence
from pathlib import Path

from src.facts.raw_repository_repository import RawCodeRepository
from src.facts.subprocess_runner import CommandResult, DefaultSubprocessRunner
from src.models.github import GitHubRepository


class FakeCloner:
    """Test cloner that writes predefined files into the checkout directory."""

    def __init__(self, files: dict[str, str]) -> None:
        self._files = files

    def clone(self, repository: GitHubRepository, destination: Path) -> None:
        for relative_path, content in self._files.items():
            file_path = destination / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)


class FakeSubprocessRunner:
    """Mocks the ``git rev-parse HEAD`` SHA lookup, delegating other commands."""

    _FAKE_SHA = "0123456789abcdef0123456789abcdef01234567"

    def __init__(self) -> None:
        self._real = DefaultSubprocessRunner()

    def run(self, args: Sequence[str], *, cwd: Path | None = None, check: bool = False) -> CommandResult:
        if list(args) == ["git", "rev-parse", "HEAD"]:
            return CommandResult(return_code=0, stdout=f"{self._FAKE_SHA}\n", stderr="")
        return self._real.run(args, cwd=cwd, check=check)


def _repository() -> GitHubRepository:
    return GitHubRepository.parse("owner/name")


def _raw_repository(cloner: FakeCloner) -> RawCodeRepository:
    return RawCodeRepository(_repository(), dep_cloner=cloner, dep_subprocess_runner=FakeSubprocessRunner())


def test_search_with_matches():
    cloner = FakeCloner({"a.py": "import os\nprint('hi')\n", "b.py": "import sys\n"})
    with _raw_repository(cloner) as repo:
        result = repo.search("import")

    assert result.pattern == "import"
    assert {str(m.path) for m in result.matches} == {"a.py", "b.py"}


def test_search_without_matches():
    cloner = FakeCloner({"a.py": "print('hi')\n"})
    with _raw_repository(cloner) as repo:
        result = repo.search("nonexistent")

    assert result.matches == []


def test_list_files_with_matches():
    cloner = FakeCloner({"a.py": "x", "b.txt": "y", "src/c.py": "z"})
    with _raw_repository(cloner) as repo:
        result = repo.list_files("*.py")

    assert [str(p) for p in result.paths] == ["a.py", "src/c.py"]


def test_list_files_without_matches():
    cloner = FakeCloner({"a.py": "x"})
    with _raw_repository(cloner) as repo:
        result = repo.list_files("*.md")

    assert result.paths == []
