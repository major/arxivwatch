"""Tests for PDF download functionality."""

import base64
import io
from unittest.mock import MagicMock, patch

import httpx
import pytest
from pypdf import PdfReader, PdfWriter

from arxivwatch.pdf import (
    download_pdf,
    encode_pdf_base64,
    extract_first_page,
    get_pdf_url,
)


def test_get_pdf_url() -> None:
    """Test converting abstract URL to PDF URL."""
    abstract_url = "http://arxiv.org/abs/2401.12345"
    expected_pdf_url = "http://arxiv.org/pdf/2401.12345.pdf"

    result = get_pdf_url(abstract_url)

    assert result == expected_pdf_url


def test_get_pdf_url_https() -> None:
    """Test converting https abstract URL to PDF URL."""
    abstract_url = "https://arxiv.org/abs/1234.5678"
    expected_pdf_url = "https://arxiv.org/pdf/1234.5678.pdf"

    result = get_pdf_url(abstract_url)

    assert result == expected_pdf_url


@patch("arxivwatch.pdf.httpx.get")
def test_download_pdf_success(mock_get: MagicMock) -> None:
    """Test successful PDF download."""
    mock_response = MagicMock()
    mock_response.content = b"fake pdf content"
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result = download_pdf("2401.12345", "http://arxiv.org/pdf/2401.12345.pdf")

    assert result == b"fake pdf content"
    mock_get.assert_called_once_with(
        "http://arxiv.org/pdf/2401.12345.pdf",
        timeout=30.0,
        follow_redirects=True,
    )
    mock_response.raise_for_status.assert_called_once()


@patch("arxivwatch.pdf.httpx.get")
def test_download_pdf_http_error(mock_get: MagicMock) -> None:
    """Test PDF download with HTTP error."""
    mock_get.side_effect = httpx.HTTPError("Network error")

    with pytest.raises(httpx.HTTPError, match="Network error"):
        download_pdf("2401.12345", "http://arxiv.org/pdf/2401.12345.pdf")


def test_encode_pdf_base64() -> None:
    """Test base64 encoding of PDF content."""
    pdf_content = b"fake pdf content"
    expected_base64 = base64.standard_b64encode(pdf_content).decode("utf-8")

    result = encode_pdf_base64(pdf_content)

    assert result == expected_base64
    assert isinstance(result, str)


def test_extract_first_page() -> None:
    """Test extracting first 5 pages from a multi-page PDF."""
    # Create a simple multi-page PDF with 10 pages
    writer = PdfWriter()

    # Add 10 blank pages
    for _ in range(10):
        writer.add_blank_page(width=612, height=792)

    # Write to bytes
    buffer = io.BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    multi_page_pdf = buffer.read()

    # Extract first 5 pages (default)
    first_pages_pdf = extract_first_page(multi_page_pdf)

    # Verify the result is a valid PDF with 5 pages
    reader = PdfReader(io.BytesIO(first_pages_pdf))
    assert len(reader.pages) == 5
    assert isinstance(first_pages_pdf, bytes)


def test_extract_first_page_fewer_than_requested() -> None:
    """Test extracting pages when PDF has fewer pages than requested."""
    # Create a simple PDF with only 3 pages
    writer = PdfWriter()

    # Add 3 blank pages
    for _ in range(3):
        writer.add_blank_page(width=612, height=792)

    # Write to bytes
    buffer = io.BytesIO()
    writer.write(buffer)
    buffer.seek(0)
    short_pdf = buffer.read()

    # Extract first 5 pages (but only 3 exist)
    extracted_pdf = extract_first_page(short_pdf, num_pages=5)

    # Verify the result contains all 3 pages
    reader = PdfReader(io.BytesIO(extracted_pdf))
    assert len(reader.pages) == 3
    assert isinstance(extracted_pdf, bytes)
