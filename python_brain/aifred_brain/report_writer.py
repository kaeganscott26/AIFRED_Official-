"""Report writer interface for preserving facts and context.

Responsibility:
    Define contracts for `.txt` and `.html` reports that preserve measured
    facts, source labels, mode, confidence, limitations, and context.

Reports must not invent advice or preserve fake meter values.
"""

from __future__ import annotations

from os import PathLike
from typing import Any


def build_report_draft(report_context: dict[str, Any]) -> dict[str, Any]:
    """Build a factual report draft from approved analysis context."""
    raise NotImplementedError("Report draft building is not implemented yet.")


def write_text_report(report_draft: dict[str, Any], destination: str | PathLike[str]) -> str:
    """Write a factual `.txt` report to an approved destination."""
    raise NotImplementedError("Text report writing is not implemented yet.")


def write_html_report(report_draft: dict[str, Any], destination: str | PathLike[str]) -> str:
    """Write a factual `.html` report to an approved destination."""
    raise NotImplementedError("HTML report writing is not implemented yet.")

