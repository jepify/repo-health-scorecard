from typing import Protocol

from src.models.metric import Scorecard


class GenerateReport(Protocol):
    """Strategy for rendering a :class:`Scorecard` into a concrete output format.

    Implementations take the shared scorecard (repository info + metric
    evaluations + weighted overall score) and produce a formatted document.
    Keeping this as a protocol lets us emit multiple formats (markdown, json,
    ...) from the same backing data without changing how scores are computed.
    """

    def generate(self, scorecard: Scorecard) -> str: ...
