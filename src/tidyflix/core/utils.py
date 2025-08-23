"""
Utility functions shared across TidyFlix modules.

This module contains common utility functions for color handling, file formatting,
directory validation, and size calculations.
"""

import argparse
import difflib
import os

from tidyflix.core.models import Colors


def highlight_changes(original: str, modified: str) -> tuple[str, str]:
    """
    Highlight changes between original and modified strings.
    Returns a tuple of (highlighted_original, highlighted_modified).
    """
    if original == modified:
        return original, modified

    # Use difflib to find character-level differences
    matcher = difflib.SequenceMatcher(None, original, modified)

    highlighted_original = ""
    highlighted_modified = ""

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            # No changes in this section
            highlighted_original += original[i1:i2]
            highlighted_modified += modified[j1:j2]
        elif tag == "delete":
            # Text was removed
            highlighted_original += f"{Colors.RED}{original[i1:i2]}{Colors.END}"
        elif tag == "insert":
            # Text was added
            highlighted_modified += f"{Colors.GREEN}{modified[j1:j2]}{Colors.END}"
        elif tag == "replace":
            # Text was changed
            highlighted_original += f"{Colors.RED}{original[i1:i2]}{Colors.END}"
            highlighted_modified += f"{Colors.GREEN}{modified[j1:j2]}{Colors.END}"

    return highlighted_original, highlighted_modified


def format_size(size_bytes: int) -> str:
    """Format size in bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)

    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1

    if i == 0:
        return f"{int(size)} {size_names[i]}"
    else:
        return f"{size:.1f} {size_names[i]}"


def get_directory_size(directory_path: str) -> int:
    """Get total size of directory in bytes using efficient os.scandir method."""
    total_size = 0
    try:
        for entry in os.scandir(directory_path):
            try:
                if entry.is_file(follow_symlinks=False):
                    total_size += entry.stat(follow_symlinks=False).st_size
                elif entry.is_dir(follow_symlinks=False):
                    total_size += get_directory_size(entry.path)
            except (OSError, PermissionError):
                # Skip files/directories that can't be accessed
                continue
    except (OSError, PermissionError):
        # Return 0 if we can't access the directory
        pass
    return total_size


def get_directory_info(directory_path: str) -> str:
    """Get directory information including size and file count."""
    if not os.path.exists(directory_path):
        return "Directory does not exist"

    if not os.path.isdir(directory_path):
        return "Not a directory"

    try:
        # Count files and subdirectories
        file_count = 0
        dir_count = 0

        for _root, dirs, files in os.walk(directory_path):
            file_count += len(files)
            dir_count += len(dirs)

        size = get_directory_size(directory_path)
        size_str = format_size(size)

        return f"{size_str}, {file_count} files, {dir_count} subdirectories"
    except (OSError, PermissionError):
        return "Permission denied"


def validate_directory(
    directory_path: str | None = None,
    operation_name: str = "process",
) -> tuple[bool, str]:
    """
    Validate that a directory exists and is accessible.

    Args:
        directory_path: Path to validate (None for current directory)
        operation_name: Name of operation for error messages (default: "process")

    Returns:
        Tuple of (is_valid, absolute_path)
        If invalid, absolute_path will be empty string
    """
    if directory_path is None:
        directory_path = os.getcwd()

    # Convert to absolute path
    abs_path = os.path.abspath(directory_path)

    if not os.path.exists(abs_path):
        print(f"Error: Cannot {operation_name} - directory '{abs_path}' does not exist.")
        return False, ""

    if not os.path.isdir(abs_path):
        print(f"Error: Cannot {operation_name} - '{abs_path}' is not a directory.")
        return False, ""

    return True, abs_path


def add_common_arguments(parser: argparse.ArgumentParser, include_explain: bool = False):
    """Add common arguments shared across normalize and clean subcommands."""
    parser.add_argument(
        "-d",
        "--directory",
        metavar="DIR",
        help="Target directory to process (default: current directory)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without actually doing it",
    )

    if include_explain:
        parser.add_argument(
            "-e",
            "--explain",
            action="store_true",
            help="Show detailed steps of how each operation is performed",
        )

    parser.add_argument("--no-color", action="store_true", help="Disable colored output")
