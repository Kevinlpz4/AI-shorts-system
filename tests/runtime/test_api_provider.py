"""
Tests for REST API TechnologyAdapter — APIProvider.

Covers:
- Missing base_url raises ValueError
- JSON response parsing
- Items extraction with items_path
- Field mapping with item_fields
- Custom transform function
- Retry logic on failure
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from runtime.providers.api.api_provider import APIProvider


class TestAPIProvider:
    """Tests for APIProvider TechnologyAdapter."""

    def test_name_property(self) -> None:
        """APIProvider has name 'api'."""
        provider = APIProvider()
        assert provider.name == "api"

    def test_fetch_requires_base_url(self) -> None:
        """APIProvider raises ValueError when 'base_url' missing."""
        provider = APIProvider()
        with pytest.raises(ValueError, match="requires 'base_url'"):
            import asyncio
            asyncio.run(provider.fetch("test", {}))

    @pytest.mark.asyncio
    async def test_fetch_with_mocked_http(self) -> None:
        """APIProvider fetches and parses JSON response."""
        provider = APIProvider()

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"title": "Item 1", "url": "https://example.com/1"},
            {"title": "Item 2", "url": "https://example.com/2"},
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("runtime.providers.api.api_provider.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=mock_response)
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = client_instance

            items = await provider.fetch("test", {"base_url": "https://api.test/data"})

        assert len(items) == 2
        assert items[0]["title"] == "Item 1"
        assert items[0]["source_id"] == "test"

    @pytest.mark.asyncio
    async def test_fetch_with_items_path(self) -> None:
        """APIProvider extracts items from nested JSON path."""
        provider = APIProvider()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "items": [
                    {"title": "Nested Item", "url": "https://example.com/nested"},
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch("runtime.providers.api.api_provider.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=mock_response)
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = client_instance

            items = await provider.fetch(
                "test",
                {"base_url": "https://api.test", "items_path": "data.items"},
            )

        assert len(items) == 1
        assert items[0]["title"] == "Nested Item"

    @pytest.mark.asyncio
    async def test_fetch_with_item_fields(self) -> None:
        """APIProvider maps output fields to JSON paths."""
        provider = APIProvider()

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"name": "repo-1", "html_url": "https://github.com/1", "stargazers_count": 100}
        ]
        mock_response.raise_for_status = MagicMock()

        with patch("runtime.providers.api.api_provider.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=mock_response)
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = client_instance

            items = await provider.fetch(
                "test",
                {
                    "base_url": "https://api.test",
                    "item_fields": {
                        "title": "name",
                        "url": "html_url",
                    },
                },
            )

        assert len(items) == 1
        assert items[0]["title"] == "repo-1"
        assert items[0]["url"] == "https://github.com/1"

    @pytest.mark.asyncio
    async def test_fetch_with_custom_transform(self) -> None:
        """APIProvider uses custom transform function when provided."""
        provider = APIProvider()

        def my_transform(raw_data, source_id):
            return [
                {"title": f"Transformed: {raw_data['key']}", "url": "https://test.com", "source_id": source_id}
            ]

        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        mock_response.raise_for_status = MagicMock()

        with patch("runtime.providers.api.api_provider.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(return_value=mock_response)
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = client_instance

            items = await provider.fetch(
                "test",
                {"base_url": "https://api.test", "transform": my_transform},
            )

        assert len(items) == 1
        assert items[0]["title"] == "Transformed: value"

    @pytest.mark.asyncio
    async def test_fetch_retry_on_failure(self) -> None:
        """APIProvider retries on HTTP failure."""
        provider = APIProvider()

        mock_response = MagicMock()
        mock_response.json.return_value = [{"title": "ok", "url": "https://ok.com"}]
        mock_response.raise_for_status = MagicMock()

        call_count = 0

        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Network error")
            return mock_response

        with patch("runtime.providers.api.api_provider.httpx.AsyncClient") as MockClient:
            client_instance = AsyncMock()
            client_instance.get = AsyncMock(side_effect=side_effect)
            client_instance.__aenter__ = AsyncMock(return_value=client_instance)
            client_instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = client_instance

            with patch("runtime.providers.api.api_provider.asyncio.sleep", new_callable=AsyncMock):
                items = await provider.fetch(
                    "test",
                    {"base_url": "https://api.test", "retry_delay": 0},
                )

        assert len(items) == 1

    def test_normalize_dict_item(self) -> None:
        """APIProvider normalizes a dict item."""
        provider = APIProvider()
        item = provider._normalize_dict("src", {"title": "T", "url": "https://x.com"})

        assert item["title"] == "T"
        assert item["url"] == "https://x.com"
        assert item["source_id"] == "src"
        assert "content_hash" in item

    def test_normalize_dict_empty(self) -> None:
        """APIProvider returns dict with defaults for item without title or url."""
        provider = APIProvider()
        item = provider._normalize_dict("src", {"other": "data"})
        # 'No title' is the default when title is missing, so item is not empty
        assert item["title"] == "No title"
        assert item["source_id"] == "src"
