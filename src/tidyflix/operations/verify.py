"""
Directory verification functions.

This module provides functionality to verify that directories contain media files.
"""

from __future__ import annotations

import os
import shutil

from tidyflix.analysis.subtitle_analyzer import is_media_file
from tidyflix.core.models import Colors
from tidyflix.core.utils import validate_directory


def verify_directories_have_media(target_directories: list[str], delete: bool = False) -> bool:
    """
    Verify that each subdirectory has at least one media file recursively.

    Args:
        target_directories: List of directories to verify
        delete: If True, delete directories that don't contain media files

    Returns True if all directories pass verification, False if any issues are found.
    """
    all_success = True
    total_checked = 0
    total_empty = 0
    total_warnings = 0

    for target_directory in target_directories:
        # Validate directory
        is_valid, validated_target_directory = validate_directory(target_directory, "verify")
        if not is_valid:
            all_success = False
            continue

        print(f"\n{Colors.CYAN}Verifying directory: {validated_target_directory}{Colors.RESET}")

        checked, empty, warnings = _process_directory(validated_target_directory, delete)
        total_checked += checked
        total_empty += empty
        total_warnings += warnings

        if empty > 0:
            all_success = False

    # Print summary
    print(f"\n{Colors.BOLD_BLUE}Summary:{Colors.RESET}")
    print(f"  Directories checked: {total_checked}")
    if total_empty == 0:
        print(f"  {Colors.GREEN}✓ All directories contain media files{Colors.RESET}")
    else:
        if delete:
            print(f"  {Colors.RED}✗ {total_empty} directories deleted{Colors.RESET}")
        else:
            print(f"  {Colors.RED}✗ {total_empty} directories without media files{Colors.RESET}")
    
    if total_warnings > 0:
        print(f"  {Colors.YELLOW}⚠ {total_warnings} directories contain archive files (rar, par2){Colors.RESET}")

    return all_success


def _process_directory(root_path: str, delete: bool = False) -> tuple[int, int, int]:
    """
    Verify immediate subdirectories for media files.

    Args:
        root_path: Root directory to verify
        delete: If True, delete directories that don't contain media files

    Returns (total_checked, empty_count, warning_count) tuple.
    """
    checked_count = 0
    empty_count = 0
    warning_count = 0

    try:
        # Get only immediate subdirectories
        immediate_subdirs = [
            item for item in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, item))
        ]
    except (PermissionError, OSError):
        print(f"  {Colors.RED}✗ Cannot access directory{Colors.RESET}")
        return 0, 0, 0

    if not immediate_subdirs:
        print(f"  {Colors.YELLOW}No subdirectories found{Colors.RESET}")
        return 0, 0, 0

    for subdir_name in sorted(immediate_subdirs):
        subdir_path = os.path.join(root_path, subdir_name)
        checked_count += 1

        # Check if this subdirectory contains archive files
        has_archives = _has_archive_files_recursive(subdir_path)
        
        # Check if this subdirectory (and its contents) has any media files
        has_media = _has_media_files_recursive(subdir_path)

        if has_archives:
            print(f"  {Colors.YELLOW}⚠ Contains archive files: {subdir_name}{Colors.RESET}")
            warning_count += 1

        if not has_media:
            # Don't delete directories with archive files, even with --delete flag
            if delete and not has_archives:
                try:
                    shutil.rmtree(subdir_path)
                    print(f"  {Colors.RED}✗ Deleted: {subdir_name}{Colors.RESET}")
                    empty_count += 1
                except OSError as e:
                    print(f"  {Colors.RED}✗ Failed to delete {subdir_name}: {e}{Colors.RESET}")
                    empty_count += 1
            else:
                if has_archives:
                    print(f"  {Colors.YELLOW}⚠ No media files (protected due to archives): {subdir_name}{Colors.RESET}")
                else:
                    print(f"  {Colors.RED}✗ No media files: {subdir_name}{Colors.RESET}")
                empty_count += 1

    return checked_count, empty_count, warning_count


def _has_media_files_recursive(directory_path: str) -> bool:
    """
    Check if a directory or any of its subdirectories contains media files.

    Args:
        directory_path: Path to the directory to check

    Returns True if any media files are found recursively, False otherwise.
    """
    try:
        for _root, _dirs, files in os.walk(directory_path):
            if any(
                is_media_file(file)
                or file.lower().endswith(".iso")
                or file.lower().endswith(".bdmv")
                for file in files
            ):
                return True
    except (PermissionError, OSError):
        # If we can't access the directory, assume it's problematic
        return False

    return False


def _has_archive_files_recursive(directory_path: str) -> bool:
    """
    Check if a directory or any of its subdirectories contains archive files (rar, par2).

    Args:
        directory_path: Path to the directory to check

    Returns True if any archive files are found recursively, False otherwise.
    """
    try:
        for _root, _dirs, files in os.walk(directory_path):
            if any(
                file.lower().endswith(".rar")
                or file.lower().endswith(".par2")
                for file in files
            ):
                return True
    except (PermissionError, OSError):
        # If we can't access the directory, assume it doesn't have archives
        return False

    return False
