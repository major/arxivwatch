"""Paper summarization using Google Gemini API."""

import base64

import google.generativeai as genai  # type: ignore[import-untyped]
import structlog

from arxivwatch.rss import Paper

logger = structlog.get_logger()


class PaperSummarizer:
    """Generates summaries of papers using Google Gemini API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        prompt_template: str,
    ) -> None:
        """Initialize the summarizer.

        Args:
            api_key: Google Gemini API key.
            model: Gemini model name to use.
            prompt_template: Prompt template with {title} placeholder.
        """
        genai.configure(api_key=api_key)  # type: ignore[attr-defined]
        self.model = genai.GenerativeModel(model)  # type: ignore[attr-defined]
        self.model_name = model
        self.prompt_template = prompt_template
        logger.info("initialized paper summarizer", model=model)

    def summarize(self, paper: Paper, pdf_base64: str) -> str:
        """Generate a summary for a paper using its PDF.

        Args:
            paper: Paper object to summarize.
            pdf_base64: Base64-encoded PDF content.

        Returns:
            Generated summary text.
        """
        try:
            prompt = self.prompt_template.format(title=paper.title)

            logger.info(
                "requesting summary from gemini",
                paper_id=paper.id,
                model=self.model_name,
            )

            # Decode base64 to bytes for Gemini
            pdf_bytes = base64.b64decode(pdf_base64)

            # Create a temporary file and upload it
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name

            # Upload PDF file
            pdf_file = genai.upload_file(  # type: ignore[attr-defined]
                path=tmp_path,
                mime_type="application/pdf",
            )

            # Generate content with PDF and prompt
            response = self.model.generate_content(
                [pdf_file, prompt],
                generation_config=genai.GenerationConfig(  # type: ignore[attr-defined]
                    max_output_tokens=4096,
                ),
            )

            summary = response.text

            # Log token usage
            usage_metadata = response.usage_metadata
            logger.info(
                "generated summary",
                paper_id=paper.id,
                summary_length=len(summary),
                input_tokens=usage_metadata.prompt_token_count,
                output_tokens=usage_metadata.candidates_token_count,
                total_tokens=usage_metadata.total_token_count,
            )

            # Clean up temporary file
            import os

            os.unlink(tmp_path)

            return summary.strip()

        except Exception as e:
            logger.error(
                "failed to generate summary",
                paper_id=paper.id,
                error=str(e),
            )
            raise
