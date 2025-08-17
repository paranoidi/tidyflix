"""
Core data models and classes for the duplicate movie detector.

This module contains the fundamental data structures used throughout the application.
"""

from __future__ import annotations

from typing_extensions import override


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output formatting."""

    RED: str = "\033[91m"
    GREEN: str = "\033[92m"
    YELLOW: str = "\033[93m"
    CYAN: str = "\033[96m"
    BLUE: str = "\033[94m"
    BOLD_BLUE: str = "\033[94;1m"
    GREY: str = "\033[2m"  # Dim/faint - should work on most terminals
    RESET: str = "\033[0m"
    # Alias for compatibility
    END: str = "\033[0m"

    @classmethod
    def disable(cls):  # pyright: ignore[reportConstantRedefinition]
        """Disable all color codes."""
        cls.RED = ""  # pyright: ignore[reportConstantRedefinition]
        cls.GREEN = ""  # pyright: ignore[reportConstantRedefinition]
        cls.YELLOW = ""  # pyright: ignore[reportConstantRedefinition]
        cls.BLUE = ""  # pyright: ignore[reportConstantRedefinition]
        cls.CYAN = ""  # pyright: ignore[reportConstantRedefinition]
        cls.GREY = ""  # pyright: ignore[reportConstantRedefinition]
        cls.BOLD_BLUE = ""  # pyright: ignore[reportConstantRedefinition]
        cls.RESET = ""  # pyright: ignore[reportConstantRedefinition]
        cls.END = ""  # pyright: ignore[reportConstantRedefinition]


class Tag:
    """Represents a video tag with color formatting and scoring."""

    def __init__(self, name: str, color: str, score: int = 0):
        """
        Initialize a Tag object.

        Args:
            name: The tag name (e.g., "H265", "4K", "HDR")
            color: The color code for display (e.g., Colors.GREEN)
            score: The scoring value for this tag (default: 0)
        """
        self.name: str = name
        self.color: str = color
        self.score: int = score

    @override
    def __str__(self) -> str:
        """Return the formatted tag string with color."""
        return f"{self.color}{self.name}{Colors.RESET}"

    @override
    def __repr__(self) -> str:
        """Return a string representation for debugging."""
        return f"Tag(name='{self.name}', color='{self.color}', score={self.score})"


class DirectoryInfo:
    """Container for pre-scanned directory information."""

    def __init__(self, name: str, abs_path: str, source_dir: str):
        self.name: str = name
        self.abs_path: str = abs_path
        self.source_dir: str = source_dir
        self.size_bytes: int | None = None
        self.size_mb: float | None = None
        self.adjusted_size_mb: float | None = None  # Size adjusted for encoding efficiency
        self.video_tags: str | None = None
        self.video_score: int | None = None  # Total score from video tags
        self.subtitle_summary: str | None = None
        self.contents: list[tuple[str, str]] | None = None  # Will store directory listing


class DuplicateGroup:
    """Container for a group of duplicate directories."""

    def __init__(self, prefix: str, directories: list[DirectoryInfo]):
        self.prefix: str = prefix
        self.directories: list[DirectoryInfo] = directories
        self.min_size_dir: DirectoryInfo | None = None
        self.max_size_dir: DirectoryInfo | None = None

    def calculate_size_info(self):
        """Calculate min/max size directories for coloring."""
        if not self.directories:
            return
        # Filter out directories without size information
        sized_dirs = [d for d in self.directories if d.size_bytes is not None]
        if not sized_dirs:
            return
        self.min_size_dir = min(sized_dirs, key=lambda x: x.size_bytes or 0)
        self.max_size_dir = max(sized_dirs, key=lambda x: x.size_bytes or 0)
