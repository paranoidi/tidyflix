"""Tests for the organize module."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from tidyflix.operations.organize import _organize_single_file, organize_media_files


def test_organize_media_files():
    """Test the organize_media_files function."""
    # This is a basic test that checks the function exists and handles empty directories
    with TemporaryDirectory() as temp_dir:
        # Test with empty directory
        success = organize_media_files([temp_dir], dry_run=True)
        assert success is True


def test_organize_single_file():
    """Test the _organize_single_file function."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a test media file
        test_file = temp_path / "Test Movie 2023.mkv"
        test_file.write_text("test content")

        # Test dry run
        result = _organize_single_file(test_file, dry_run=True)
        assert result is True
        assert test_file.exists()  # File should still exist in dry run

        # Test actual move
        result = _organize_single_file(test_file, dry_run=False)
        assert result is True
        assert not test_file.exists()  # Original file should be gone

        # Check if file was moved to correct location
        expected_dir = temp_path / "Test.Movie.2023"
        expected_file = expected_dir / "Test Movie 2023.mkv"
        assert expected_file.exists()
        assert expected_file.read_text() == "test content"
