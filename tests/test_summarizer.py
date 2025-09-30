"""Tests for paper summarization."""

from unittest.mock import MagicMock, patch

import pytest

from arxivwatch.rss import Paper
from arxivwatch.summarizer import PaperSummarizer


@pytest.fixture
def sample_paper() -> Paper:
    """Create a sample paper for testing."""
    return Paper(
        id="2401.12345",
        title="Test Paper Title",
        abstract="This is a test abstract with important findings.",
        link="http://arxiv.org/abs/2401.12345",
        authors=["John Doe", "Jane Smith"],
        published="2024-01-15T10:00:00Z",
    )


@patch("arxivwatch.summarizer.genai.configure")
@patch("arxivwatch.summarizer.genai.GenerativeModel")
def test_summarizer_initialization(
    mock_model_class: MagicMock, mock_configure: MagicMock
) -> None:
    """Test that the summarizer initializes correctly."""
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model

    summarizer = PaperSummarizer(
        api_key="test-api-key",
        model="gemini-2.5-flash-lite",
        prompt_template="Summarize: {title}",
    )

    assert summarizer.model_name == "gemini-2.5-flash-lite"
    assert summarizer.prompt_template == "Summarize: {title}"
    mock_configure.assert_called_once_with(api_key="test-api-key")
    mock_model_class.assert_called_once_with("gemini-2.5-flash-lite")


@patch("arxivwatch.summarizer.genai.configure")
@patch("arxivwatch.summarizer.genai.GenerativeModel")
@patch("arxivwatch.summarizer.genai.upload_file")
def test_summarize_paper(
    mock_upload: MagicMock,
    mock_model_class: MagicMock,
    mock_configure: MagicMock,
    sample_paper: Paper,
) -> None:
    """Test summarizing a paper."""
    # Setup mock model and response
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model

    mock_response = MagicMock()
    mock_response.text = "This is a generated summary of the paper."
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.prompt_token_count = 1000
    mock_response.usage_metadata.candidates_token_count = 200
    mock_response.usage_metadata.total_token_count = 1200
    mock_model.generate_content.return_value = mock_response

    mock_pdf_file = MagicMock()
    mock_upload.return_value = mock_pdf_file

    summarizer = PaperSummarizer(
        api_key="test-api-key",
        model="gemini-2.5-flash-lite",
        prompt_template="Title: {title}",
    )

    pdf_base64 = "ZmFrZSBwZGYgY29udGVudA=="  # "fake pdf content" in base64
    summary = summarizer.summarize(sample_paper, pdf_base64)

    assert summary == "This is a generated summary of the paper."
    mock_upload.assert_called_once()
    mock_model.generate_content.assert_called_once()


@patch("arxivwatch.summarizer.genai.configure")
@patch("arxivwatch.summarizer.genai.GenerativeModel")
@patch("arxivwatch.summarizer.genai.upload_file")
def test_summarize_with_custom_prompt(
    mock_upload: MagicMock,
    mock_model_class: MagicMock,
    mock_configure: MagicMock,
    sample_paper: Paper,
) -> None:
    """Test that the prompt template is correctly formatted."""
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model

    mock_response = MagicMock()
    mock_response.text = "Custom summary."
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.prompt_token_count = 500
    mock_response.usage_metadata.candidates_token_count = 100
    mock_response.usage_metadata.total_token_count = 600
    mock_model.generate_content.return_value = mock_response

    mock_pdf_file = MagicMock()
    mock_upload.return_value = mock_pdf_file

    prompt_template = "Paper: {title}"
    summarizer = PaperSummarizer(
        api_key="test-api-key",
        model="gemini-2.5-flash-lite",
        prompt_template=prompt_template,
    )

    pdf_base64 = "ZmFrZSBwZGYgY29udGVudA=="
    summarizer.summarize(sample_paper, pdf_base64)

    # Check that generate_content was called with correct prompt
    call_args = mock_model.generate_content.call_args
    content_list = call_args[0][0]
    assert "Test Paper Title" in content_list[1]


@patch("arxivwatch.summarizer.genai.configure")
@patch("arxivwatch.summarizer.genai.GenerativeModel")
@patch("arxivwatch.summarizer.genai.upload_file")
def test_summarize_api_error_raises(
    mock_upload: MagicMock,
    mock_model_class: MagicMock,
    mock_configure: MagicMock,
    sample_paper: Paper,
) -> None:
    """Test that API errors are raised."""
    mock_model = MagicMock()
    mock_model_class.return_value = mock_model
    mock_model.generate_content.side_effect = Exception("API Error")

    mock_pdf_file = MagicMock()
    mock_upload.return_value = mock_pdf_file

    summarizer = PaperSummarizer(
        api_key="test-api-key",
        model="gemini-2.5-flash-lite",
        prompt_template="{title}",
    )

    pdf_base64 = "ZmFrZSBwZGYgY29udGVudA=="
    with pytest.raises(Exception, match="API Error"):
        summarizer.summarize(sample_paper, pdf_base64)
