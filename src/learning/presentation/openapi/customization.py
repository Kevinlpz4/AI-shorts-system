"""
OpenAPI schema customization for the Learning Intelligence API.

Customizes the auto-generated OpenAPI schema with tags, descriptions,
and metadata for the Learning Intelligence endpoints.
"""
from __future__ import annotations

from typing import Any


def customize_openapi(tags: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return OpenAPI schema customizations.

    Args:
        tags: Optional list of tag definitions.

    Returns:
        Dictionary with OpenAPI schema overrides.
    """
    return {
        "tags": tags or [
            {
                "name": "Health",
                "description": "Health, readiness, and liveness probes.",
            },
            {
                "name": "Prediction",
                "description": "Predict content approval based on statistical signals.",
            },
            {
                "name": "Explanation",
                "description": "Explain why an article received its score.",
            },
            {
                "name": "Recommendation",
                "description": "Generate editorial recommendations with reasoning.",
            },
            {
                "name": "Feedback",
                "description": "Record human decisions on content.",
            },
            {
                "name": "Source Intelligence",
                "description": "Get comprehensive quality intelligence for content sources.",
            },
            {
                "name": "Knowledge",
                "description": "Summary of all accumulated knowledge.",
            },
            {
                "name": "Timeline",
                "description": "Query historical evolution of knowledge metrics.",
            },
            {
                "name": "Signals",
                "description": "Query active learning signals with optional filters.",
            },
            {
                "name": "Datasets",
                "description": "List and export versioned training datasets.",
            },
            {
                "name": "Artifacts",
                "description": "List knowledge artifacts with version history.",
            },
            {
                "name": "Analytics",
                "description": "Comprehensive learning analytics and progress metrics.",
            },
        ],
    }
