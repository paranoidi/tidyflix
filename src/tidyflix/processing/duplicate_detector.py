"""
Duplicate detection and prefix parsing functions.

This module handles the identification of duplicate movie directories
based on naming patterns and year detection.
"""

import os
import re
from collections import defaultdict

from tidyflix.core.models import Colors, DirectoryInfo


def parse_prefix(name: str) -> str | None:
    """Extract prefix including the 4-digit year."""
    match = re.search(r"\b\d{4}\b", name)
    if match:
        return name[: match.end()].strip().replace(".", " ")
    return None


def discover_duplicates(target_dirs: list[str]) -> dict[str, list[DirectoryInfo]]:
    """Phase 1: Quick discovery of directories and identification of duplicates."""
    print(
        f"\n{Colors.CYAN}Phase 1: Discovering directories and identifying duplicates...{Colors.RESET}"
    )

    # Collect all directories and group by prefix (lightweight pass)
    prefix_groups: defaultdict[str, list[DirectoryInfo]] = defaultdict(list)

    for target_dir in target_dirs:
        abs_target_dir = os.path.abspath(target_dir)
        try:
            for item in os.listdir(target_dir):
                item_path = os.path.join(target_dir, item)
                if os.path.isdir(item_path):
                    dir_info = DirectoryInfo(
                        name=item, abs_path=os.path.abspath(item_path), source_dir=abs_target_dir
                    )

                    prefix = parse_prefix(dir_info.name)
                    if prefix:
                        prefix_groups[prefix].append(dir_info)
        except (PermissionError, OSError) as e:
            print(f"Warning: Cannot access directory {target_dir}: {e}")
            continue

    # Filter to only groups with duplicates
    duplicate_groups: dict[str, list[DirectoryInfo]] = {
        prefix: dlist for prefix, dlist in prefix_groups.items() if len(dlist) > 1
    }

    if not duplicate_groups:
        print("No duplicates found.")
        return {}

    # Count directories for user info
    total_dirs = sum(len(dlist) for dlist in prefix_groups.values())
    directories_to_scan = sum(len(dlist) for dlist in duplicate_groups.values())

    print(
        f"Found {total_dirs} total directories, {directories_to_scan} need analysis ({len(duplicate_groups)} duplicates)."
    )
    print(f"{Colors.CYAN}Starting background analysis and interactive processing...{Colors.RESET}")

    return duplicate_groups
