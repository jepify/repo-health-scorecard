import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel


class CommandResult(BaseModel):
    """The captured outcome of running a subprocess command."""

    return_code: int
    stdout: str
    stderr: str


class SubprocessRunner(Protocol):
    """Runs a subprocess command and returns its captured output.

    Injected into components that shell out (e.g. the RawCode repository) so
    they can be tested without touching the real process/filesystem.
    """

    def run(self, args: Sequence[str], *, cwd: Path | None = None, check: bool = False) -> CommandResult: ...


class DefaultSubprocessRunner:
    """Default :class:`SubprocessRunner` backed by :mod:`subprocess`.

    Always captures stdout/stderr as text. When ``check`` is ``True`` a
    non-zero exit raises :class:`subprocess.CalledProcessError`.
    """

    def run(self, args: Sequence[str], *, cwd: Path | None = None, check: bool = False) -> CommandResult:
        completed = subprocess.run(
            list(args),
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True,
        )
        return CommandResult(
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
