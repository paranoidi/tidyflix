"""Tests for duplicate detection functionality."""

from __future__ import annotations

import os
import tempfile

from tidyflix.processing.duplicate_detector import discover_duplicates, parse_prefix


def test_parse_prefix():
    """Test parse_prefix function."""
    assert parse_prefix("Some Movie 2023") == "Some Movie 2023"
    assert parse_prefix("Some.Movie.2023") == "Some Movie 2023"
    # parse_prefix extracts up to and including the year, so parentheses after year are not included
    assert parse_prefix("Movie Title (1999)") == "Movie Title (1999"
    assert parse_prefix("No Year Here") is None
    assert parse_prefix("2023") == "2023"


def test_case_insensitive_duplicate_detection():
    """Test that duplicate detection groups directories with different capitalization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directories with different capitalization
        dir1 = os.path.join(temp_dir, "Some Movie 2023")
        dir2 = os.path.join(temp_dir, "Some movie 2023")
        dir3 = os.path.join(temp_dir, "SOME MOVIE 2023")
        dir4 = os.path.join(temp_dir, "Different Movie 2023")

        os.makedirs(dir1)
        os.makedirs(dir2)
        os.makedirs(dir3)
        os.makedirs(dir4)

        # Discover duplicates
        duplicate_groups = discover_duplicates([temp_dir])

        # Should find one group with 3 directories (all variations of "Some Movie 2023")
        assert len(duplicate_groups) == 1

        # Get the group
        group_key = list(duplicate_groups.keys())[0]
        assert group_key == "some movie 2023"  # Normalized to lowercase

        # Should have 3 directories in the group
        directories = duplicate_groups[group_key]
        assert len(directories) == 3

        # Verify all three variations are present
        dir_names = {d.name for d in directories}
        assert "Some Movie 2023" in dir_names
        assert "Some movie 2023" in dir_names
        assert "SOME MOVIE 2023" in dir_names


def test_case_insensitive_duplicate_detection_mixed_cases():
    """Test duplicate detection with various capitalization patterns."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directories with various capitalization
        dir1 = os.path.join(temp_dir, "Some Movie 1999")
        dir2 = os.path.join(temp_dir, "some movie 1999")
        dir3 = os.path.join(temp_dir, "SOME MOVIE 1999")
        dir4 = os.path.join(temp_dir, "Some Movie Sequel 2003")

        os.makedirs(dir1)
        os.makedirs(dir2)
        os.makedirs(dir3)
        os.makedirs(dir4)

        duplicate_groups = discover_duplicates([temp_dir])

        # Should find one group with 3 directories (all variations of "Some Movie 1999")
        assert len(duplicate_groups) == 1

        group_key = list(duplicate_groups.keys())[0]
        assert group_key == "some movie 1999"

        directories = duplicate_groups[group_key]
        assert len(directories) == 3

        dir_names = {d.name for d in directories}
        assert "Some Movie 1999" in dir_names
        assert "some movie 1999" in dir_names
        assert "SOME MOVIE 1999" in dir_names


def test_case_insensitive_duplicate_detection_no_duplicates():
    """Test that different movies are not grouped together."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directories with different movie names (same year)
        dir1 = os.path.join(temp_dir, "Movie A 2023")
        dir2 = os.path.join(temp_dir, "Movie B 2023")
        dir3 = os.path.join(temp_dir, "Movie C 2023")

        os.makedirs(dir1)
        os.makedirs(dir2)
        os.makedirs(dir3)

        duplicate_groups = discover_duplicates([temp_dir])

        # Should find no duplicates (each movie is different)
        assert len(duplicate_groups) == 0


def test_case_insensitive_duplicate_detection_with_dots():
    """Test duplicate detection with dot-separated names."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create directories with dots and different capitalization
        dir1 = os.path.join(temp_dir, "Some.Movie.2023")
        dir2 = os.path.join(temp_dir, "some.movie.2023")
        dir3 = os.path.join(temp_dir, "SOME.MOVIE.2023")

        os.makedirs(dir1)
        os.makedirs(dir2)
        os.makedirs(dir3)

        duplicate_groups = discover_duplicates([temp_dir])

        # Should find one group with 3 directories
        assert len(duplicate_groups) == 1

        group_key = list(duplicate_groups.keys())[0]
        assert group_key == "some movie 2023"  # Dots replaced with spaces, normalized

        directories = duplicate_groups[group_key]
        assert len(directories) == 3
