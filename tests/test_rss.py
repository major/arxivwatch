"""Tests for RSS feed parsing."""

from unittest.mock import MagicMock, patch

import pytest
import feedparser

from arxivwatch.rss import RSSFeedParser


@pytest.fixture
def mock_feed_entry() -> feedparser.FeedParserDict:
    """Create a mock feed entry."""
    entry = feedparser.FeedParserDict()
    entry["id"] = "http://arxiv.org/abs/2401.12345"
    entry["title"] = "Test Paper Title"
    entry["summary"] = "This is a test abstract."
    entry["link"] = "http://arxiv.org/abs/2401.12345"
    entry["authors"] = [{"name": "John Doe"}, {"name": "Jane Smith"}]
    entry["published"] = "2024-01-15T10:00:00Z"
    entry["tags"] = [{"term": "cs.AI"}, {"term": "cs.LG"}]
    return entry


@pytest.fixture
def mock_feed(mock_feed_entry: feedparser.FeedParserDict) -> feedparser.FeedParserDict:
    """Create a mock feed with entries."""
    feed = feedparser.FeedParserDict()
    feed.entries = [mock_feed_entry]  # type: ignore[attr-defined]
    return feed


def test_parse_entry(mock_feed_entry: feedparser.FeedParserDict) -> None:
    """Test parsing a single feed entry."""
    parser = RSSFeedParser([])
    paper = parser._parse_entry(mock_feed_entry)

    assert paper.id == "2401.12345"
    assert paper.title == "Test Paper Title"
    assert paper.abstract == "This is a test abstract."
    assert paper.link == "http://arxiv.org/abs/2401.12345"
    assert paper.authors == ["John Doe", "Jane Smith"]
    assert paper.published == "2024-01-15T10:00:00Z"
    assert paper.categories == ["cs.AI", "cs.LG"]
    assert paper.announce_type is None


def test_parse_entry_without_authors() -> None:
    """Test parsing an entry without authors."""
    entry = feedparser.FeedParserDict()
    entry["id"] = "http://arxiv.org/abs/2401.12345"
    entry["title"] = "Test Paper"
    entry["summary"] = "Abstract"
    entry["link"] = "http://arxiv.org/abs/2401.12345"
    entry["authors"] = []
    entry["published"] = "2024-01-15T10:00:00Z"

    parser = RSSFeedParser([])
    paper = parser._parse_entry(entry)

    assert paper.authors == []


@pytest.mark.parametrize(
    "paper_id_format,expected_id",
    [
        ("http://arxiv.org/abs/2401.12345", "2401.12345"),
        ("https://arxiv.org/abs/1234.5678v2", "1234.5678v2"),
        ("arxiv:2401.12345", "arxiv:2401.12345"),  # Fallback for unusual format
    ],
)
def test_parse_various_id_formats(paper_id_format: str, expected_id: str) -> None:
    """Test parsing various paper ID formats."""
    entry = feedparser.FeedParserDict()
    entry["id"] = paper_id_format
    entry["title"] = "Test"
    entry["summary"] = "Abstract"
    entry["link"] = "http://example.com"
    entry["authors"] = []
    entry["published"] = "2024-01-15T10:00:00Z"

    parser = RSSFeedParser([])
    paper = parser._parse_entry(entry)

    assert paper.id == expected_id


@patch("arxivwatch.rss.feedparser.parse")
def test_fetch_papers_single_feed(
    mock_parse: MagicMock,
    mock_feed: feedparser.FeedParserDict,
) -> None:
    """Test fetching papers from a single feed."""
    mock_parse.return_value = mock_feed

    parser = RSSFeedParser(["http://example.com/feed"])
    papers = parser.fetch_papers()

    assert len(papers) == 1
    assert papers[0].id == "2401.12345"
    assert papers[0].title == "Test Paper Title"
    mock_parse.assert_called_once_with("http://example.com/feed")


@patch("arxivwatch.rss.feedparser.parse")
def test_fetch_papers_multiple_feeds(mock_parse: MagicMock) -> None:
    """Test fetching papers from multiple feeds."""
    # Create two different mock feeds
    feed1 = feedparser.FeedParserDict()
    entry1 = feedparser.FeedParserDict()
    entry1["id"] = "http://arxiv.org/abs/2401.11111"
    entry1["title"] = "Paper 1"
    entry1["summary"] = "Abstract 1"
    entry1["link"] = "http://arxiv.org/abs/2401.11111"
    entry1["authors"] = []
    entry1["published"] = "2024-01-15T10:00:00Z"
    feed1.entries = [entry1]  # type: ignore[attr-defined]

    feed2 = feedparser.FeedParserDict()
    entry2 = feedparser.FeedParserDict()
    entry2["id"] = "http://arxiv.org/abs/2401.22222"
    entry2["title"] = "Paper 2"
    entry2["summary"] = "Abstract 2"
    entry2["link"] = "http://arxiv.org/abs/2401.22222"
    entry2["authors"] = []
    entry2["published"] = "2024-01-15T11:00:00Z"
    feed2.entries = [entry2]  # type: ignore[attr-defined]

    mock_parse.side_effect = [feed1, feed2]

    parser = RSSFeedParser(["http://example.com/feed1", "http://example.com/feed2"])
    papers = parser.fetch_papers()

    assert len(papers) == 2
    assert papers[0].id == "2401.11111"
    assert papers[1].id == "2401.22222"


@patch("arxivwatch.rss.feedparser.parse")
def test_fetch_papers_handles_feed_error(mock_parse: MagicMock) -> None:
    """Test that errors in one feed don't stop processing others."""
    feed = feedparser.FeedParserDict()
    entry = feedparser.FeedParserDict()
    entry["id"] = "http://arxiv.org/abs/2401.12345"
    entry["title"] = "Good Paper"
    entry["summary"] = "Abstract"
    entry["link"] = "http://arxiv.org/abs/2401.12345"
    entry["authors"] = []
    entry["published"] = "2024-01-15T10:00:00Z"
    feed.entries = [entry]  # type: ignore[attr-defined]

    # First feed raises an error, second feed succeeds
    mock_parse.side_effect = [Exception("Feed error"), feed]

    parser = RSSFeedParser(["http://bad-feed.com", "http://good-feed.com"])
    papers = parser.fetch_papers()

    # Should still get the paper from the good feed
    assert len(papers) == 1
    assert papers[0].id == "2401.12345"


def test_parse_entry_with_html_in_abstract() -> None:
    """Test that HTML tags are stripped from abstracts."""
    entry = feedparser.FeedParserDict()
    entry["id"] = "http://arxiv.org/abs/2401.12345"
    entry["title"] = "Test Paper"
    entry["summary"] = (
        "<p>arXiv:2401.12345 [cs.AI] This is an <b>abstract</b> with <i>HTML</i> tags.</p>"
    )
    entry["link"] = "http://arxiv.org/abs/2401.12345"
    entry["authors"] = []
    entry["published"] = "2024-01-15T10:00:00Z"

    parser = RSSFeedParser([])
    paper = parser._parse_entry(entry)

    # Should have HTML stripped and arXiv ID prefix removed
    assert paper.abstract == "This is an abstract with HTML tags."


def test_parse_entry_with_categories() -> None:
    """Test parsing categories from tags."""
    entry = feedparser.FeedParserDict()
    entry["id"] = "http://arxiv.org/abs/2401.12345"
    entry["title"] = "Test Paper"
    entry["summary"] = "Abstract"
    entry["link"] = "http://arxiv.org/abs/2401.12345"
    entry["authors"] = []
    entry["published"] = "2024-01-15T10:00:00Z"
    entry["tags"] = [{"term": "cs.AI"}, {"term": "cs.LG"}, {"term": "stat.ML"}]

    parser = RSSFeedParser([])
    paper = parser._parse_entry(entry)

    assert paper.categories == ["cs.AI", "cs.LG", "stat.ML"]
