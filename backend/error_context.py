from __future__ import annotations

import linecache
import traceback
from typing import Any


def format_exception_with_context(exc: BaseException) -> tuple[str, dict[str, Any] | None]:
    """Return a formatted traceback string and context for the innermost frame."""

    tb_exception = traceback.TracebackException.from_exception(exc)
    formatted = "".join(tb_exception.format())

    innermost = _find_innermost_exception(tb_exception)
    if not innermost or not innermost.stack:
        return formatted, None

    frame_summary = innermost.stack[-1]
    source_lines = _gather_source_context(frame_summary.filename, frame_summary.lineno)

    context = {
        "file": frame_summary.filename,
        "line": frame_summary.lineno,
        "function": frame_summary.name,
        "source": source_lines,
    }

    return formatted, context


def _find_innermost_exception(tb_exception: traceback.TracebackException | None) -> traceback.TracebackException | None:
    current = tb_exception
    while current is not None:
        next_exception = current.__cause__ or current.__context__
        if next_exception is None:
            return current
        current = next_exception
    return None


def _gather_source_context(filename: str, center_line: int, radius: int = 2) -> list[dict[str, Any]]:
    """Collect source lines surrounding ``center_line`` from ``filename``."""

    start = max(1, center_line - radius)
    end = max(center_line + radius, center_line)
    lines: list[dict[str, Any]] = []

    for lineno in range(start, end + 1):
        text = linecache.getline(filename, lineno)
        lines.append({
            "line": lineno,
            "code": text.rstrip("\n") if text else "",
            "highlight": lineno == center_line,
        })

    return lines

