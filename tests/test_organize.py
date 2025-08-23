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


def test_organize_skips_tv_episodes():
    """Test that organize_media_files skips TV episode files matching the regex pattern."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create TV episode files that should be skipped
        tv_files = [
            "Show.S01E01.mkv",
            "Series S1E1 Episode.avi",
            "Test.S12E123.mp4",
            "Movie S2E05 Title.mkv",
            " S01E01 .mp4",  # With spaces
            ".S1E1.mkv",  # With dots
            "Movie with S01E01 in title.mkv",  # Pattern surrounded by spaces
        ]

        # Create regular movie files that should be organized
        movie_files = [
            "Regular Movie 2023.mkv",
            "Another Film.avi",
        ]

        # Create all test files
        for filename in tv_files + movie_files:
            test_file = temp_path / filename
            test_file.write_text("test content")

        # Run organize in dry run mode
        success = organize_media_files([str(temp_path)], dry_run=True)
        assert success is True

        # Verify TV episode files still exist (not moved)
        for filename in tv_files:
            test_file = temp_path / filename
            assert test_file.exists(), f"TV episode file {filename} should not be moved"

        # Verify movie files still exist (would be moved in non-dry run)
        for filename in movie_files:
            test_file = temp_path / filename
            assert test_file.exists(), f"Movie file {filename} should exist"


def test_organize_processes_non_tv_episodes():
    """Test that organize_media_files processes non-TV episode files normally."""
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create files that should NOT match the TV episode pattern
        non_tv_files = [
            "MovieS01E01Title.mkv",  # Pattern not surrounded by spaces/dots
            "SomeShow.2023.mkv",  # No episode pattern
            "Series Season 1.mkv",  # Written out, not S1E1 format
            "Test.S1.mkv",  # Missing episode number
            "Test.E01.mkv",  # Missing season number
        ]

        # Create all test files
        for filename in non_tv_files:
            test_file = temp_path / filename
            test_file.write_text("test content")

        # Run organize (actual move, not dry run)
        success = organize_media_files([str(temp_path)], dry_run=False)
        assert success is True

        # Verify files were moved (original files should not exist)
        for filename in non_tv_files:
            original_file = temp_path / filename
            assert not original_file.exists(), f"Original file {filename} should be moved"

            # Check that organized directory was created
            stem = Path(filename).stem.replace(" ", ".")
            organized_dir = temp_path / stem
            organized_file = organized_dir / filename
            assert organized_file.exists(), (
                f"Organized file {filename} should exist in subdirectory"
            )
