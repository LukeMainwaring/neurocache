"""Tests for message serialization utilities."""

from neurocache.utils.message_serialization import _extract_web_sources_from_content


class TestExtractWebSourcesFromContent:
    def test_extracts_url_and_title(self) -> None:
        content = {
            "status": "completed",
            "sources": [
                {"type": "url", "url": "https://example.com/article", "title": "Example Article"},
                {"type": "url", "url": "https://other.com"},
            ],
        }
        result = _extract_web_sources_from_content(content)

        assert len(result) == 2
        assert result[0] == {"url": "https://example.com/article", "title": "Example Article"}
        assert result[1] == {"url": "https://other.com"}

    def test_empty_sources_list(self) -> None:
        content = {"status": "completed", "sources": []}
        assert _extract_web_sources_from_content(content) == []

    def test_no_sources_key(self) -> None:
        content = {"status": "completed"}
        assert _extract_web_sources_from_content(content) == []

    def test_non_dict_content_returns_empty(self) -> None:
        assert _extract_web_sources_from_content("not a dict") == []
        assert _extract_web_sources_from_content(None) == []

    def test_skips_items_without_url(self) -> None:
        content = {
            "status": "completed",
            "sources": [
                {"type": "url", "url": "https://valid.com"},
                {"type": "text", "content": "no url here"},
            ],
        }
        result = _extract_web_sources_from_content(content)

        assert len(result) == 1
        assert result[0]["url"] == "https://valid.com"
