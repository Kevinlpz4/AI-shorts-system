"""
Private URL validation utilities — shared by SourceUrl and ArticleUrl.

This module is INTERNAL to the domain layer. It is NOT exported from
the value_objects package. It exists solely to eliminate the ~80% code
duplication between SourceUrl and ArticleUrl without over-engineering a
public base class.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from ingestion.domain.exceptions import IngestionError

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")


def validate_url(
    value: str,
    *,
    error_cls: type[IngestionError],
    field_name: str = "URL",
) -> str:
    """Validate and normalize a URL string.

    Performs the common validations shared by SourceUrl and ArticleUrl:
      - Not empty / not whitespace-only
      - No control characters
      - Must have http or https scheme
      - Must have a valid domain (netloc)

    Args:
        value: The URL string to validate.
        error_cls: The exception class to raise on validation failure
            (e.g. ``InvalidSourceUrlError`` or ``InvalidArticleUrlError``).
        field_name: Human-readable field name for error messages.

    Returns:
        The stripped URL value.

    Raises:
        IngestionError: Subclass determined by ``error_cls`` on validation
            failure. Also a ``ValueError`` for backward compatibility.
    """
    stripped = value.strip() if value else value

    if not stripped:
        raise error_cls(f"{field_name} must not be empty")

    if _CONTROL_CHARS_RE.search(stripped):
        raise error_cls(f"{field_name} must not contain control characters")

    parsed = urlparse(stripped)

    if parsed.scheme not in ("http", "https"):
        raise error_cls(
            f"{field_name} scheme must be http or https, got '{parsed.scheme}'"
        )

    if not parsed.netloc:
        raise error_cls(f"{field_name} must have a valid domain")

    return stripped
