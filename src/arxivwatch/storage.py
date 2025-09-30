"""Storage management for tracking notified paper IDs."""

import json
from pathlib import Path

import structlog

logger = structlog.get_logger()


class PaperStorage:
    """Manages storage of notified paper IDs in a JSON file."""

    def __init__(self, storage_path: str | Path) -> None:
        """Initialize storage with a file path.

        Args:
            storage_path: Path to the JSON file for storing paper IDs.
        """
        self.storage_path = Path(storage_path)
        logger.info("initialized paper storage", path=str(self.storage_path))

    def load_notified_ids(self) -> set[str]:
        """Load the set of previously notified paper IDs.

        Returns:
            Set of paper IDs that have been notified.
        """
        if not self.storage_path.exists():
            logger.info("no existing storage file found, starting fresh")
            return set()

        try:
            with self.storage_path.open("r") as f:
                data = json.load(f)
                notified_ids = set(data.get("notified_ids", []))
                logger.info("loaded notified paper ids", count=len(notified_ids))
                return notified_ids
        except (json.JSONDecodeError, OSError) as e:
            logger.error(
                "failed to load storage file",
                error=str(e),
                path=str(self.storage_path),
            )
            return set()

    def save_notified_ids(self, notified_ids: set[str]) -> None:
        """Save the set of notified paper IDs.

        Args:
            notified_ids: Set of paper IDs that have been notified.
        """
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with self.storage_path.open("w") as f:
                json.dump(
                    {"notified_ids": sorted(notified_ids)},
                    f,
                    indent=2,
                )
            logger.info("saved notified paper ids", count=len(notified_ids))
        except OSError as e:
            logger.error(
                "failed to save storage file",
                error=str(e),
                path=str(self.storage_path),
            )
            raise

    def add_notified_id(self, paper_id: str) -> None:
        """Add a paper ID to the notified set.

        Args:
            paper_id: The paper ID to mark as notified.
        """
        notified_ids = self.load_notified_ids()
        notified_ids.add(paper_id)
        self.save_notified_ids(notified_ids)
