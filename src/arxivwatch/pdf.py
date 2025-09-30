"""PDF download utilities for arXiv papers."""

import base64
import io

import httpx
import structlog
from pypdf import PdfReader, PdfWriter

logger = structlog.get_logger()


def get_pdf_url(arxiv_url: str) -> str:
    """Convert arXiv abstract URL to PDF URL.

    Args:
        arxiv_url: arXiv abstract URL (e.g., http://arxiv.org/abs/2401.12345)

    Returns:
        arXiv PDF URL (e.g., http://arxiv.org/pdf/2401.12345.pdf)
    """
    return arxiv_url.replace("/abs/", "/pdf/") + ".pdf"


def download_pdf(paper_id: str, pdf_url: str) -> bytes:
    """Download PDF from arXiv.

    Args:
        paper_id: Paper ID for logging.
        pdf_url: URL to PDF file.

    Returns:
        PDF content as bytes.

    Raises:
        httpx.HTTPError: If download fails.
    """
    logger.info("downloading pdf", paper_id=paper_id, url=pdf_url)

    try:
        response = httpx.get(pdf_url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()

        logger.info(
            "downloaded pdf",
            paper_id=paper_id,
            size_bytes=len(response.content),
        )

        return response.content

    except httpx.HTTPError as e:
        logger.error(
            "failed to download pdf",
            paper_id=paper_id,
            url=pdf_url,
            error=str(e),
        )
        raise


def extract_first_page(pdf_content: bytes, num_pages: int = 5) -> bytes:
    """Extract the first N pages from a PDF.

    Args:
        pdf_content: Full PDF content as bytes.
        num_pages: Number of pages to extract (default: 5).

    Returns:
        First N pages PDF content as bytes.
    """
    reader = PdfReader(io.BytesIO(pdf_content))
    writer = PdfWriter()

    # Add first N pages (or fewer if PDF is shorter)
    pages_to_extract = min(num_pages, len(reader.pages))
    for i in range(pages_to_extract):
        writer.add_page(reader.pages[i])

    logger.info(
        "extracted pages from pdf",
        total_pages=len(reader.pages),
        extracted_pages=pages_to_extract,
    )

    # Write to bytes
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)

    return output_buffer.read()


def encode_pdf_base64(pdf_content: bytes) -> str:
    """Encode PDF content as base64 string.

    Args:
        pdf_content: Raw PDF bytes.

    Returns:
        Base64-encoded string.
    """
    return base64.standard_b64encode(pdf_content).decode("utf-8")
