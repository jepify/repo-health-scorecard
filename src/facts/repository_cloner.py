from pathlib import Path
from typing import Protocol

from src.facts.subprocess_runner import DefaultSubprocessRunner, SubprocessRunner
from src.models.github import GitHubRepository


class RepositoryCloner(Protocol):
    """Makes a repository's ``HEAD`` available in a local destination folder.

    Injected into :class:`RawCodeRepository` so tests can populate the checkout
    with plain files instead of performing a real clone.
    """

    def clone(self, repository: GitHubRepository, destination: Path) -> None: ...


class ShallowGitRepositoryCloner:
    """Default cloner: shallow-clones ``HEAD`` via ``git`` (see ADR 003)."""

    def __init__(self, dep_subprocess_runner: SubprocessRunner | None = None) -> None:
        self._subprocess_runner = dep_subprocess_runner or DefaultSubprocessRunner()

    def clone(self, repository: GitHubRepository, destination: Path) -> None:
        print("Cloning repository:", repository.clone_url)
        self._subprocess_runner.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--single-branch",
                repository.clone_url,
                str(destination),
            ],
            check=True,
        )
