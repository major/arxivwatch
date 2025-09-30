"""Main orchestration for arXiv paper watching and notification."""

import sys

import structlog

from arxivwatch.config import get_settings
from arxivwatch.notifier import EmailNotifier
from arxivwatch.pdf import (
    download_pdf,
    encode_pdf_base64,
    extract_first_page,
    get_pdf_url,
)
from arxivwatch.rss import RSSFeedParser
from arxivwatch.storage import PaperStorage
from arxivwatch.summarizer import PaperSummarizer

# Configure structlog for human-readable stdout logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)

logger = structlog.get_logger()


def main() -> None:
    """Main entry point for the arXiv watcher."""
    try:
        logger.info("starting arxiv watcher")

        # Load configuration
        settings = get_settings()
        logger.info("loaded configuration", feed_count=len(settings.rss_urls))

        # Initialize components
        storage = PaperStorage(settings.storage_file)
        rss_parser = RSSFeedParser(settings.rss_urls)
        summarizer = PaperSummarizer(
            api_key=settings.gemini_api_key.get_secret_value(),
            model=settings.gemini_model,
            prompt_template=settings.gemini_prompt,
        )
        notifier = EmailNotifier(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_username=settings.smtp_username,
            smtp_password=settings.smtp_password.get_secret_value(),
            from_address=str(settings.smtp_from),
            to_addresses=[str(settings.smtp_to)],
        )

        # Load previously notified paper IDs
        notified_ids = storage.load_notified_ids()
        is_first_run = len(notified_ids) == 0

        # Fetch papers from RSS feeds
        papers = rss_parser.fetch_papers()

        if not papers:
            logger.info("no papers found in feeds")
            return

        # Filter out already notified papers
        new_papers = [p for p in papers if p.id not in notified_ids]

        logger.info(
            "filtered papers",
            total_papers=len(papers),
            new_papers=len(new_papers),
            is_first_run=is_first_run,
        )

        # On first run, only notify for the latest paper but mark all as seen
        papers_to_process = new_papers
        if is_first_run and new_papers:
            logger.info(
                "first run detected, processing only the latest paper but marking all as seen"
            )
            # Sort by published date (most recent first) and take the first one for processing
            papers_to_process = sorted(
                new_papers,
                key=lambda p: p.published,
                reverse=True,
            )[:1]
            # Mark all papers as notified to prevent re-processing on next run
            for paper in new_papers:
                notified_ids.add(paper.id)

        # Process each new paper
        for paper in papers_to_process:
            try:
                logger.info("processing paper", paper_id=paper.id, title=paper.title)

                # Download PDF and extract first N pages
                pdf_url = get_pdf_url(paper.link)
                pdf_content = download_pdf(paper.id, pdf_url)
                first_pages = extract_first_page(
                    pdf_content, num_pages=settings.gemini_pdf_pages
                )
                pdf_base64 = encode_pdf_base64(first_pages)

                # Generate summary
                summary = summarizer.summarize(paper, pdf_base64)

                # Send notification
                notifier.send_notification(paper, summary)

                # Mark as notified (unless already marked in first run)
                if not is_first_run:
                    notified_ids.add(paper.id)

                logger.info("successfully processed paper", paper_id=paper.id)

            except Exception as e:
                logger.error(
                    "failed to process paper",
                    paper_id=paper.id,
                    error=str(e),
                )
                # Continue with next paper even if one fails

        # Save updated notified IDs
        storage.save_notified_ids(notified_ids)

        logger.info(
            "arxiv watcher completed",
            papers_processed=len(new_papers),
            total_notified=len(notified_ids),
        )

    except Exception as e:
        logger.error("arxiv watcher failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
