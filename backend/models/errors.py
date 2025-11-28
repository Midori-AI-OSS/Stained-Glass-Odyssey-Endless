"""Standardized error models for backend error handling with persistence."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Any
from typing import Optional
import uuid

from pydantic import BaseModel
from pydantic import Field


class ErrorSeverity(str, Enum):
    """Severity levels for error classification."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorSource(BaseModel):
    """A single line of source code context around an error."""

    line: int
    code: str
    highlight: bool = False


class ErrorContext(BaseModel):
    """Context information about where an error occurred."""

    file: str
    line: int
    function: Optional[str] = None
    source: list[ErrorSource] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Standardized error response format for API responses."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: ErrorSeverity = ErrorSeverity.ERROR
    message: str
    traceback: Optional[str] = None
    context: Optional[ErrorContext] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PersistedErrors(BaseModel):
    """Collection of errors persisted to disk for crash recovery."""

    errors: list[ErrorResponse] = Field(default_factory=list)
    last_crash: Optional[datetime] = None


def error_context_from_dict(ctx: dict[str, Any] | None) -> ErrorContext | None:
    """Convert a context dict from format_exception_with_context to ErrorContext."""
    if ctx is None:
        return None

    source_lines: list[ErrorSource] = []
    raw_source = ctx.get("source", [])
    if isinstance(raw_source, list):
        for item in raw_source:
            if isinstance(item, dict):
                source_lines.append(
                    ErrorSource(
                        line=item.get("line", 0),
                        code=item.get("code", ""),
                        highlight=bool(item.get("highlight", False)),
                    )
                )

    return ErrorContext(
        file=ctx.get("file", ""),
        line=ctx.get("line", 0),
        function=ctx.get("function"),
        source=source_lines,
    )


def create_error_response(
    message: str,
    traceback_text: str | None = None,
    context: dict[str, Any] | None = None,
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    exc_type: str | None = None,
) -> ErrorResponse:
    """Create an ErrorResponse from exception details.

    Args:
        message: Human-readable error message
        traceback_text: Formatted traceback string
        context: Context dict from format_exception_with_context
        severity: Error severity level
        exc_type: Exception type name for metadata

    Returns:
        Fully populated ErrorResponse instance
    """
    metadata: dict[str, Any] = {}
    if exc_type:
        metadata["type"] = exc_type

    return ErrorResponse(
        severity=severity,
        message=message,
        traceback=traceback_text,
        context=error_context_from_dict(context),
        metadata=metadata,
    )
