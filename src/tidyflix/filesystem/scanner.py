"""
File system scanning and directory analysis functions.

This module handles directory size calculation, content scanning,
and directory information gathering.
"""

import os

from tidyflix.analysis.subtitle_analyzer import get_directory_subtitles
from tidyflix.analysis.video_analyzer import (
    calculate_adjusted_size,
    format_video_tags,
    parse_video_tags_with_score,
)
from tidyflix.core.models import DirectoryInfo
from tidyflix.core.utils import get_directory_size as get_dir_size


def get_directory_contents_cached(directory: str) -> list[tuple[str, str]]:
    """Get cached directory contents for display."""
    try:
        contents = os.listdir(directory)
        files: list[str] = []
        dirs: list[str] = []

        # Separate files and directories
        for item in sorted(contents):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path):
                files.append(item)
            elif os.path.isdir(item_path):
                dirs.append(item)

        result: list[tuple[str, str]] = []
        # Add first 10 files
        for item in files[:10]:
            result.append(("file", item))

        # Add summary for remaining files
        remaining_files = len(files) - 10
        if remaining_files > 0:
            result.append(("summary", f"[{remaining_files} more files ...]"))

        # Add directories
        for item in dirs:
            result.append(("dir", item))
            # Get subdirectory contents recursively
            subdir_path = os.path.join(directory, item)
            try:
                sub_contents = os.listdir(subdir_path)
                sub_files = [
                    f for f in sub_contents if os.path.isfile(os.path.join(subdir_path, f))
                ]
                sub_dirs = [d for d in sub_contents if os.path.isdir(os.path.join(subdir_path, d))]

                # Add first few items from subdirectory
                for sub_item in sorted(sub_files[:5]):
                    result.append(("subfile", sub_item))
                for sub_item in sorted(sub_dirs[:3]):
                    result.append(("subdir", sub_item))

                remaining_sub_items = len(sub_files) + len(sub_dirs) - 8
                if remaining_sub_items > 0:
                    result.append(("subsummary", f"[{remaining_sub_items} more items ...]"))
            except (PermissionError, OSError):
                result.append(("error", "[Permission denied]"))

        return result
    except (PermissionError, OSError) as e:
        return [("error", f"[Error reading contents: {e}]")]


def scan_directory_info(
    dir_info: DirectoryInfo, language_filter: list[str] | None = None
) -> DirectoryInfo:
    """Scan all information for a single directory."""
    # Calculate directory size
    dir_info.size_bytes = get_dir_size(dir_info.abs_path)
    dir_info.size_mb = dir_info.size_bytes / (1024 * 1024)

    # Get video tags and tag-only score
    tag_objects, tag_score = parse_video_tags_with_score(
        dir_info.name,
        dir_info.abs_path,
        size_mb=0,  # Don't include size scoring yet
    )
    dir_info.video_tags = format_video_tags(tag_objects)
    dir_info.video_score = tag_score  # Just tag score for now

    # Calculate adjusted size for encoding efficiency
    dir_info.adjusted_size_mb = calculate_adjusted_size(dir_info.size_mb, tag_objects)

    # Get subtitle summary
    dir_info.subtitle_summary = get_directory_subtitles(dir_info.abs_path, language_filter)

    # Cache directory contents for display
    dir_info.contents = get_directory_contents_cached(dir_info.abs_path)

    return dir_info
