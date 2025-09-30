"""Tests for email notification."""

from unittest.mock import MagicMock, patch

import pytest

from arxivwatch.notifier import EmailNotifier
from arxivwatch.rss import Paper


@pytest.fixture
def sample_paper() -> Paper:
    """Create a sample paper for testing."""
    return Paper(
        id="2401.12345",
        title="Test Paper Title",
        abstract="This is a test abstract.",
        link="http://arxiv.org/abs/2401.12345",
        authors=["John Doe", "Jane Smith"],
        published="2024-01-15T10:00:00Z",
    )


@pytest.fixture
def notifier() -> EmailNotifier:
    """Create an EmailNotifier instance."""
    return EmailNotifier(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password="password",
        from_address="sender@example.com",
        to_addresses=["recipient@example.com"],
    )


def test_notifier_initialization() -> None:
    """Test that the notifier initializes correctly."""
    notifier = EmailNotifier(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password="password",
        from_address="sender@example.com",
        to_addresses=["recipient1@example.com", "recipient2@example.com"],
    )

    assert notifier.smtp_host == "smtp.example.com"
    assert notifier.smtp_port == 587
    assert notifier.smtp_username == "user@example.com"
    assert notifier.smtp_password == "password"
    assert notifier.from_address == "sender@example.com"
    assert len(notifier.to_addresses) == 2


def test_create_text_body(notifier: EmailNotifier, sample_paper: Paper) -> None:
    """Test creating plain text email body."""
    summary = "This is a test summary."
    body = notifier._create_text_body(sample_paper, summary)

    assert "Test Paper Title" in body
    assert "John Doe, Jane Smith" in body
    assert "2024-01-15T10:00:00Z" in body
    assert summary in body
    assert sample_paper.link in body


def test_create_text_body_no_authors(notifier: EmailNotifier) -> None:
    """Test creating text body for paper without authors."""
    paper = Paper(
        id="2401.12345",
        title="No Authors Paper",
        abstract="Abstract",
        link="http://arxiv.org/abs/2401.12345",
        authors=[],
        published="2024-01-15T10:00:00Z",
    )

    body = notifier._create_text_body(paper, "Summary")
    assert "Unknown" in body


def test_create_message(notifier: EmailNotifier, sample_paper: Paper) -> None:
    """Test creating email message."""
    summary = "This is a test summary."
    message = notifier._create_message(sample_paper, summary)

    assert message["Subject"] == "Test Paper Title"
    assert message["From"] == "sender@example.com"
    assert message["To"] == "recipient@example.com"

    # Check that message has both text and HTML parts
    assert message.get_content_type() == "multipart/alternative"
    parts = list(message.walk())
    content_types = [p.get_content_type() for p in parts]
    assert "text/plain" in content_types
    assert "text/html" in content_types


def test_create_message_multiple_recipients(sample_paper: Paper) -> None:
    """Test creating message for multiple recipients."""
    notifier = EmailNotifier(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
        smtp_password="password",
        from_address="sender@example.com",
        to_addresses=["recipient1@example.com", "recipient2@example.com"],
    )

    message = notifier._create_message(sample_paper, "Summary")
    assert "recipient1@example.com" in message["To"]
    assert "recipient2@example.com" in message["To"]


@patch("arxivwatch.notifier.smtplib.SMTP")
def test_send_notification(
    mock_smtp_class: MagicMock,
    notifier: EmailNotifier,
    sample_paper: Paper,
) -> None:
    """Test sending an email notification."""
    mock_server = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_server

    summary = "This is a test summary."
    notifier.send_notification(sample_paper, summary)

    # Verify SMTP connection was made
    mock_smtp_class.assert_called_once_with("smtp.example.com", 587)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user@example.com", "password")
    mock_server.send_message.assert_called_once()


@patch("arxivwatch.notifier.smtplib.SMTP")
def test_send_notification_smtp_error(
    mock_smtp_class: MagicMock,
    notifier: EmailNotifier,
    sample_paper: Paper,
) -> None:
    """Test that SMTP errors are raised."""
    mock_smtp_class.return_value.__enter__.side_effect = Exception("SMTP Error")

    with pytest.raises(Exception, match="SMTP Error"):
        notifier.send_notification(sample_paper, "Summary")
