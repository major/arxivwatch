"""RSS feed fetching and parsing for arXiv papers."""

import re
from dataclasses import dataclass

import feedparser
import structlog

logger = structlog.get_logger()


@dataclass
class Paper:
    """Represents an arXiv paper from an RSS feed."""

    id: str
    title: str
    abstract: str
    link: str
    authors: list[str]
    published: str
    categories: list[str] = None  # type: ignore[assignment]
    announce_type: str | None = None

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.categories is None:
            self.categories = []


class RSSFeedParser:
    """Fetches and parses arXiv RSS feeds."""

    def __init__(self, feed_urls: list[str]) -> None:
        """Initialize with a list of RSS feed URLs.

        Args:
            feed_urls: List of arXiv RSS feed URLs to monitor.
        """
        self.feed_urls = feed_urls
        logger.info("initialized rss feed parser", feed_count=len(feed_urls))

    def fetch_papers(self) -> list[Paper]:
        """Fetch papers from all configured RSS feeds.

        Returns:
            List of Paper objects from all feeds.
        """
        all_papers: list[Paper] = []

        for url in self.feed_urls:
            try:
                papers = self._parse_feed(url)
                all_papers.extend(papers)
                logger.info(
                    "fetched papers from feed",
                    url=url,
                    count=len(papers),
                )
            except Exception as e:
                logger.error(
                    "failed to fetch feed",
                    url=url,
                    error=str(e),
                )

        logger.info("fetched all papers", total_count=len(all_papers))
        return all_papers

    def _parse_feed(self, url: str) -> list[Paper]:
        """Parse a single RSS feed.

        Args:
            url: RSS feed URL to parse.

        Returns:
            List of Paper objects from the feed.
        """
        feed = feedparser.parse(url)

        papers: list[Paper] = []
        for entry in feed.entries:
            try:
                paper = self._parse_entry(entry)
                papers.append(paper)
            except Exception as e:
                logger.error(
                    "failed to parse entry",
                    entry_id=getattr(entry, "id", "unknown"),
                    error=str(e),
                )

        return papers

    def _parse_entry(self, entry: feedparser.FeedParserDict) -> Paper:
        """Parse a single feed entry into a Paper object.

        Args:
            entry: Feed entry from feedparser.

        Returns:
            Paper object with extracted data.
        """
        # Extract paper ID from the entry id (usually in format: http://arxiv.org/abs/XXXX.XXXXX)
        paper_id = entry.id.split("/abs/")[-1] if "abs" in entry.id else entry.id  # type: ignore[union-attr]

        # Extract authors (dc:creator or authors field)
        authors = []
        if hasattr(entry, "authors") and entry.authors:
            authors = [
                author.get("name", "")
                for author in entry.get("authors", [])  # type: ignore[union-attr]
            ]
        elif hasattr(entry, "author"):
            # Fallback to single author field
            authors = [entry.author]  # type: ignore[list-item]

        # Extract abstract from summary, cleaning HTML if present
        abstract = entry.get("summary", "")
        if abstract:
            # arXiv RSS often includes HTML tags and extra formatting
            # Extract just the abstract text, removing arXiv ID prefix
            abstract = re.sub(
                r"<[^>]+>", "", str(abstract)
            )  # Remove HTML tags  # type: ignore[arg-type]
            # Remove common prefixes like "arXiv:XXXX.XXXXX [category]"
            abstract = re.sub(r"^arXiv:\d+\.\d+v?\d*\s*\[[^\]]+\]\s*", "", abstract)
            abstract = abstract.strip()

        # Extract categories (tags in feedparser)
        categories = []
        if hasattr(entry, "tags"):
            categories = [tag.get("term", "") for tag in entry.tags]  # type: ignore[union-attr]

        # Extract announce_type from arxiv namespace if available
        announce_type = None
        if hasattr(entry, "arxiv_announce_type"):
            announce_type = entry.arxiv_announce_type  # type: ignore[attr-defined]

        return Paper(
            id=paper_id,  # type: ignore[arg-type]
            title=entry.title.strip(),  # type: ignore[union-attr]
            abstract=str(abstract) if abstract else "",  # type: ignore[arg-type]
            link=entry.link,  # type: ignore[arg-type]
            authors=authors,  # type: ignore[arg-type]
            published=entry.get("published", ""),  # type: ignore[arg-type]
            categories=categories,  # type: ignore[arg-type]
            announce_type=str(announce_type) if announce_type else None,  # type: ignore[arg-type]
        )
