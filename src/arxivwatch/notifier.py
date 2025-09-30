"""Email notification for paper summaries."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import markdown
import structlog

from arxivwatch.rss import Paper

logger = structlog.get_logger()


class EmailNotifier:
    """Sends email notifications for paper summaries."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        from_address: str,
        to_addresses: list[str],
    ) -> None:
        """Initialize the email notifier.

        Args:
            smtp_host: SMTP server hostname.
            smtp_port: SMTP server port.
            smtp_username: SMTP authentication username.
            smtp_password: SMTP authentication password.
            from_address: From email address.
            to_addresses: List of recipient email addresses.
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_address = from_address
        self.to_addresses = to_addresses
        logger.info(
            "initialized email notifier",
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            recipient_count=len(to_addresses),
        )

    def send_notification(self, paper: Paper, summary: str) -> None:
        """Send an email notification for a paper.

        Args:
            paper: Paper object with metadata.
            summary: Generated summary text.
        """
        try:
            message = self._create_message(paper, summary)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)

            logger.info(
                "sent email notification",
                paper_id=paper.id,
                paper_title=paper.title,
                recipient_count=len(self.to_addresses),
            )

        except Exception as e:
            logger.error(
                "failed to send email",
                paper_id=paper.id,
                error=str(e),
            )
            raise

    def _create_message(self, paper: Paper, summary: str) -> MIMEMultipart:
        """Create an email message for a paper.

        Args:
            paper: Paper object with metadata.
            summary: Generated summary text.

        Returns:
            Email message ready to send.
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = paper.title
        message["From"] = self.from_address
        message["To"] = ", ".join(self.to_addresses)

        # Create both plain text and HTML versions
        text_body = self._create_text_body(paper, summary)
        html_body = self._create_html_body(paper, summary)

        message.attach(MIMEText(text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        return message

    def _create_text_body(self, paper: Paper, summary: str) -> str:
        """Create plain text email body.

        Args:
            paper: Paper object with metadata.
            summary: Generated summary text.

        Returns:
            Plain text email body.
        """
        authors_str = ", ".join(paper.authors) if paper.authors else "Unknown"

        return f"""New arXiv Paper: {paper.title}

Authors: {authors_str}
Published: {paper.published}

Summary:
{summary}

Read the full paper: {paper.link}
"""

    def _create_html_body(self, paper: Paper, summary: str) -> str:
        """Create HTML email body.

        Args:
            paper: Paper object with metadata.
            summary: Generated summary text.

        Returns:
            HTML email body.
        """
        authors_str = ", ".join(paper.authors) if paper.authors else "Unknown"

        # Convert markdown to HTML
        md = markdown.Markdown(extensions=["extra", "nl2br", "sane_lists"])
        summary_html = md.convert(summary)

        return f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            margin: 0 0 15px 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .metadata {{
            font-size: 14px;
            opacity: 0.95;
        }}
        .metadata p {{
            margin: 5px 0;
        }}
        .summary {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            margin: 20px 0;
        }}
        .summary h2 {{
            margin-top: 0;
            color: #667eea;
            font-size: 20px;
        }}
        .summary h3, .summary h4 {{
            color: #667eea;
            margin: 20px 0 10px 0;
        }}
        .summary p {{
            margin: 15px 0;
            line-height: 1.8;
        }}
        .summary ul, .summary ol {{
            margin: 15px 0;
            padding-left: 25px;
            line-height: 1.8;
        }}
        .summary li {{
            margin: 8px 0;
        }}
        .summary strong {{
            color: #333;
            font-weight: 600;
        }}
        .summary code {{
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .summary pre {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            line-height: 1.5;
        }}
        .summary blockquote {{
            border-left: 3px solid #667eea;
            padding-left: 15px;
            margin: 15px 0;
            color: #666;
            font-style: italic;
        }}
        .link {{
            margin-top: 30px;
            text-align: center;
        }}
        .link a {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 500;
            transition: background 0.3s ease;
        }}
        .link a:hover {{
            background: #764ba2;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{paper.title}</h1>
        <div class="metadata">
            <p><strong>Authors:</strong> {authors_str}</p>
            <p><strong>Published:</strong> {paper.published}</p>
        </div>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        {summary_html}
    </div>

    <div class="link">
        <a href="{paper.link}">Read Full Paper on arXiv</a>
    </div>
</body>
</html>
"""
