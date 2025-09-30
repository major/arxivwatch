"""Configuration management using pydantic-settings."""

from pathlib import Path
from typing import Any

from pydantic import EmailStr, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="ARXIV_", env_file=".env")

    # RSS Feed Configuration
    rss_urls: list[str] = Field(
        description="List of arXiv RSS feed URLs or shorthand names (e.g., 'cs.AI' or full URL)",
        default=["cs.AI", "cs.CE", "q-fin", "stat.ML", "econ"],
    )

    @field_validator("rss_urls", mode="after")
    @classmethod
    def expand_rss_urls(cls, v: list[str]) -> list[str]:
        """Expand shorthand RSS feed names to full URLs."""
        base_url = "https://rss.arxiv.org/rss/"
        expanded = []
        for url in v:
            # If it doesn't look like a URL, treat it as a shorthand
            if not url.startswith(("http://", "https://")):
                expanded.append(f"{base_url}{url}")
            else:
                expanded.append(url)
        return expanded

    # Gemini API Configuration
    gemini_api_key: SecretStr = Field(
        description="Google Gemini API key",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash-lite",
        description="Gemini model to use for summaries",
    )
    gemini_prompt_file: str | None = Field(
        default=None,
        description="Path to file containing prompt template (overrides gemini_prompt if set)",
    )
    gemini_prompt: str = Field(
        default=(
            "Summarize this research paper concisely. "
            "Highlight the main contributions, methodology, and key findings. "
            "Keep it under 200 words.\n\nTitle: {title}"
        ),
        description="Prompt template for Gemini (supports {title} placeholder)",
    )
    gemini_pdf_pages: int = Field(
        default=20,
        description="Number of pages from the PDF to send to Gemini (default: 5)",
    )

    @field_validator("gemini_prompt", mode="after")
    @classmethod
    def load_prompt_from_file(cls, v: str, info: Any) -> str:  # type: ignore[misc]
        """Load prompt from file if gemini_prompt_file is specified."""
        # Get the prompt_file value from the model data
        prompt_file = info.data.get("gemini_prompt_file")  # type: ignore[union-attr]
        if prompt_file:
            prompt_path = Path(prompt_file)
            if prompt_path.exists():
                return prompt_path.read_text().strip()
            raise ValueError(f"Prompt file not found: {prompt_file}")
        return v

    # SMTP Configuration
    smtp_host: str = Field(
        description="SMTP server hostname",
    )
    smtp_port: int = Field(
        default=587,
        description="SMTP server port",
    )
    smtp_username: str = Field(
        description="SMTP authentication username",
    )
    smtp_password: SecretStr = Field(
        description="SMTP authentication password",
    )
    smtp_from: EmailStr = Field(
        description="From email address",
    )
    smtp_to: list[EmailStr] = Field(
        description="List of recipient email addresses",
    )

    # Storage Configuration
    storage_file: str = Field(
        default="notified_papers.json",
        description="File to store notified paper IDs",
    )


def get_settings() -> Settings:
    """Get the application settings."""
    return Settings()  # type: ignore[call-arg]
