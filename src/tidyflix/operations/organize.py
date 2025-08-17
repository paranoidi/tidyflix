"""
Media file organization functionality.

This module provides functionality to organize media files by moving them
into subdirectories based on their filenames.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from tidyflix.core.config import MEDIA_EXTENSIONS
from tidyflix.core.models import Colors


def organize_media_files(target_directories: list[str], dry_run: bool = False) -> bool:
    """
    Organize media files by moving them into subdirectories.

    For each media file, creates a subdirectory with the same name as the file
    (without extension, with spaces replaced by dots) and moves the file into it.

    Args:
        target_directories: List of directory paths to process
        dry_run: If True, show what would be done without actually doing it

    Returns:
        True if successful, False if any errors occurred
    """
    success = True
    total_moved = 0

    for directory in target_directories:
        dir_path = Path(directory).resolve()
        print(f"{Colors.CYAN}Processing directory: {dir_path}{Colors.RESET}")

        if not dir_path.exists():
            print(f"{Colors.RED}Error: Directory '{dir_path}' does not exist{Colors.RESET}")
            success = False
            continue

        if not dir_path.is_dir():
            print(f"{Colors.RED}Error: '{dir_path}' is not a directory{Colors.RESET}")
            success = False
            continue

        # Find all media files in the directory
        media_files: list[Path] = []
        for file_path in dir_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in MEDIA_EXTENSIONS:
                media_files.append(file_path)

        if not media_files:
            print(f"  No media files found in {dir_path}")
            continue

        print(f"  Found {len(media_files)} media file(s)")

        # Process each media file
        for file_path in media_files:
            moved = _organize_single_file(file_path, dry_run)
            if moved:
                total_moved += 1

    # Summary
    if dry_run:
        print(
            f"\n{Colors.CYAN}Dry run complete. {total_moved} file(s) would be organized.{Colors.RESET}"
        )
    else:
        print(
            f"\n{Colors.GREEN}Organization complete. {total_moved} file(s) moved successfully.{Colors.RESET}"
        )

    return success


def _organize_single_file(file_path: Path, dry_run: bool) -> bool:
    """
    Organize a single media file by moving it to a subdirectory.

    Args:
        file_path: Path to the media file
        dry_run: If True, show what would be done without actually doing it

    Returns:
        True if file was moved (or would be moved in dry run), False otherwise
    """
    # Create subdirectory name from filename
    file_name_without_extension = file_path.stem
    # Replace spaces with dots to match common media naming conventions
    subdir_name = file_name_without_extension.replace(" ", ".")

    # Create destination directory path
    destination_dir = file_path.parent / subdir_name
    destination_file = destination_dir / file_path.name

    # Check if destination already exists
    if destination_file.exists():
        print(
            f"  {Colors.YELLOW}Skipping {file_path.name} - destination already exists{Colors.RESET}"
        )
        return False

    if dry_run:
        print(f"  {Colors.BLUE}Would create:{Colors.RESET} {destination_dir}")
        print(f"  {Colors.BLUE}Would move:{Colors.RESET} {file_path.name} -> {destination_dir}")
        return True

    try:
        # Create the destination directory if it doesn't exist
        if not destination_dir.exists():
            print(f"  {Colors.GREEN}Creating:{Colors.RESET} {destination_dir}")
            destination_dir.mkdir(parents=True, exist_ok=True)

        # Move the file to the destination directory
        print(f"  {Colors.GREEN}Moving:{Colors.RESET} {file_path.name} -> {destination_dir}")
        shutil.move(str(file_path), str(destination_file))
        return True

    except (OSError, shutil.Error) as e:
        print(f"  {Colors.RED}FAILED:{Colors.RESET} Could not move {file_path.name} - {e}")
        return False
