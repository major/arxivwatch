"""Tests for paper storage functionality."""

import json
from pathlib import Path

import pytest

from arxivwatch.storage import PaperStorage


@pytest.fixture
def temp_storage_file(tmp_path: Path) -> Path:
    """Create a temporary storage file path."""
    return tmp_path / "test_storage.json"


@pytest.fixture
def storage(temp_storage_file: Path) -> PaperStorage:
    """Create a PaperStorage instance with a temporary file."""
    return PaperStorage(temp_storage_file)


def test_load_notified_ids_nonexistent_file(storage: PaperStorage) -> None:
    """Test loading from a non-existent file returns empty set."""
    ids = storage.load_notified_ids()
    assert ids == set()


def test_save_and_load_notified_ids(storage: PaperStorage) -> None:
    """Test saving and loading paper IDs."""
    test_ids = {"1234.5678", "9876.5432"}
    storage.save_notified_ids(test_ids)

    loaded_ids = storage.load_notified_ids()
    assert loaded_ids == test_ids


def test_add_notified_id(storage: PaperStorage) -> None:
    """Test adding a single paper ID."""
    storage.add_notified_id("1234.5678")

    loaded_ids = storage.load_notified_ids()
    assert "1234.5678" in loaded_ids


def test_add_multiple_notified_ids(storage: PaperStorage) -> None:
    """Test adding multiple paper IDs sequentially."""
    storage.add_notified_id("1234.5678")
    storage.add_notified_id("9876.5432")

    loaded_ids = storage.load_notified_ids()
    assert loaded_ids == {"1234.5678", "9876.5432"}


def test_storage_file_format(storage: PaperStorage, temp_storage_file: Path) -> None:
    """Test that the storage file has the correct JSON format."""
    test_ids = {"1234.5678", "9876.5432"}
    storage.save_notified_ids(test_ids)

    with temp_storage_file.open("r") as f:
        data = json.load(f)

    assert "notified_ids" in data
    assert set(data["notified_ids"]) == test_ids
    # Check that IDs are sorted in the file
    assert data["notified_ids"] == sorted(test_ids)


@pytest.mark.parametrize(
    "paper_ids",
    [
        set(),  # Empty set
        {"single_id"},  # Single ID
        {"id1", "id2", "id3"},  # Multiple IDs
        {f"id{i}" for i in range(100)},  # Many IDs
    ],
)
def test_save_load_various_sizes(storage: PaperStorage, paper_ids: set[str]) -> None:
    """Test saving and loading various sizes of paper ID sets."""
    storage.save_notified_ids(paper_ids)
    loaded_ids = storage.load_notified_ids()
    assert loaded_ids == paper_ids


def test_corrupted_file_returns_empty_set(temp_storage_file: Path) -> None:
    """Test that a corrupted file returns an empty set."""
    # Write invalid JSON to the file
    temp_storage_file.write_text("not valid json {{{")

    storage = PaperStorage(temp_storage_file)
    ids = storage.load_notified_ids()
    assert ids == set()
