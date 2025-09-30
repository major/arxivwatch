"""Tests for configuration."""

from arxivwatch.config import Settings


def test_rss_urls_shorthand_expansion(monkeypatch):
    """Test that shorthand RSS URLs are expanded."""
    monkeypatch.setenv("ARXIV_RSS_URLS", '["cs.AI", "cs.LG"]')
    monkeypatch.setenv("ARXIV_CLAUDE_API_KEY", "test-key")
    monkeypatch.setenv("ARXIV_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("ARXIV_SMTP_USERNAME", "user")
    monkeypatch.setenv("ARXIV_SMTP_PASSWORD", "pass")
    monkeypatch.setenv("ARXIV_SMTP_FROM", "from@example.com")
    monkeypatch.setenv("ARXIV_SMTP_TO", '["to@example.com"]')

    settings = Settings()  # type: ignore[call-arg]

    assert settings.rss_urls == [
        "https://rss.arxiv.org/rss/cs.AI",
        "https://rss.arxiv.org/rss/cs.LG",
    ]


def test_rss_urls_full_urls_preserved(monkeypatch):
    """Test that full URLs are preserved as-is."""
    monkeypatch.setenv(
        "ARXIV_RSS_URLS",
        '["https://rss.arxiv.org/rss/cs.AI", "https://example.com/feed.xml"]',
    )
    monkeypatch.setenv("ARXIV_CLAUDE_API_KEY", "test-key")
    monkeypatch.setenv("ARXIV_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("ARXIV_SMTP_USERNAME", "user")
    monkeypatch.setenv("ARXIV_SMTP_PASSWORD", "pass")
    monkeypatch.setenv("ARXIV_SMTP_FROM", "from@example.com")
    monkeypatch.setenv("ARXIV_SMTP_TO", '["to@example.com"]')

    settings = Settings()  # type: ignore[call-arg]

    assert settings.rss_urls == [
        "https://rss.arxiv.org/rss/cs.AI",
        "https://example.com/feed.xml",
    ]


def test_rss_urls_mixed(monkeypatch):
    """Test mixing shorthand and full URLs."""
    monkeypatch.setenv("ARXIV_RSS_URLS", '["cs.AI", "https://example.com/feed.xml"]')
    monkeypatch.setenv("ARXIV_CLAUDE_API_KEY", "test-key")
    monkeypatch.setenv("ARXIV_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("ARXIV_SMTP_USERNAME", "user")
    monkeypatch.setenv("ARXIV_SMTP_PASSWORD", "pass")
    monkeypatch.setenv("ARXIV_SMTP_FROM", "from@example.com")
    monkeypatch.setenv("ARXIV_SMTP_TO", '["to@example.com"]')

    settings = Settings()  # type: ignore[call-arg]

    assert settings.rss_urls == [
        "https://rss.arxiv.org/rss/cs.AI",
        "https://example.com/feed.xml",
    ]
