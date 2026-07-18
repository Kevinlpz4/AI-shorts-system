"""
RFC 9457 Problem Details — standardized error responses.

Every error from the Learning Intelligence API returns a ProblemDetails
body with type, title, status, detail, and optional validation errors.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ProblemDetails(BaseModel):
    """RFC 9457 compliant Problem Details for HTTP APIs.

    Attributes:
        type: URI reference identifying the problem type (default: "about:blank").
        title: Short human-readable summary of the problem.
        status: HTTP status code.
        detail: Human-readable explanation specific to this occurrence.
        instance: URI reference identifying the specific occurrence.
        errors: Validation errors keyed by field name.
    """

    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: str = ""
    errors: dict[str, list[str]] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "about:blank",
                    "title": "Validation Error",
                    "status": 422,
                    "detail": "Request body contains invalid fields",
                    "instance": "/api/v1/learning/predict",
                    "errors": {
                        "source_name": ["Field required"],
                    },
                }
            ]
        }
    }
