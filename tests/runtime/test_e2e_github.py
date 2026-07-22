"""
E2E test for GitHub API — real external call.

Validates:
- GitHub search API is reachable
- Repository search works
- At least 1 valid repo is returned
- Repo has required fields
"""
from __future__ import annotations

import pytest

import httpx

from runtime.providers.api.github import github_transform


@pytest.mark.asyncio
async def test_github_api_e2e() -> None:
    """E2E: Fetch real GitHub trending repositories."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.github.com/search/repositories?q=created:>2026-07-01&sort=stars&order=desc&per_page=5",
            timeout=30,
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        resp.raise_for_status()
        raw_data = resp.json()

    items = github_transform(raw_data, "github-e2e")

    assert len(items) >= 1, f"Expected at least 1 repo, got {len(items)}"

    # Validate first item
    first = items[0]
    assert first["title"], "Repo must have a title"
    assert first["url"].startswith("http"), "Repo must have a URL"
    assert first["source_id"] == "github-e2e"
    assert "gh_stars" in first, "Repo must have gh_stars"
    assert "gh_language" in first, "Repo must have gh_language"

    print(f"✅ GitHub API: {len(items)} repos fetched successfully")
    print(f"   First repo: {first['title'][:80]}...")
    print(f"   Stars: {first['gh_stars']}, Language: {first['gh_language']}")
