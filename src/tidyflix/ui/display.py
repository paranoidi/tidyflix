"""
Display and formatting functions for user interface.

This module handles terminal output formatting, color coding,
and content display for the duplicate detector.
"""

from tidyflix.analysis.subtitle_analyzer import is_subtitle_file
from tidyflix.core.config import DEFAULT_INDENT
from tidyflix.core.models import Colors, DirectoryInfo


def get_size_color(
    dir_info: DirectoryInfo, min_size_dir: DirectoryInfo, max_size_dir: DirectoryInfo
) -> str:
    """Get color based on directory size."""
    if dir_info.name == max_size_dir.name:
        return Colors.GREEN
    elif dir_info.name == min_size_dir.name:
        return Colors.RED
    else:
        return Colors.YELLOW


def list_directory_contents_cached(
    cached_contents: list[tuple[str, str]], indent: str = DEFAULT_INDENT
):
    """List and display directory contents using cached data."""
    for content_type, item in cached_contents:
        if content_type == "file":
            if is_subtitle_file(item):
                print(f"{indent}- {Colors.BLUE}{item}{Colors.RESET}")
            else:
                print(f"{indent}- {Colors.GREY}{item}{Colors.RESET}")
        elif content_type == "summary":
            print(f"{indent}{item}")
        elif content_type == "dir":
            print(f"{indent}- {Colors.GREY}{item}/{Colors.RESET}")
        elif content_type == "subfile":
            if is_subtitle_file(item):
                print(f"{indent}  - {Colors.BLUE}{item}{Colors.RESET}")
            else:
                print(f"{indent}  - {Colors.GREY}{item}{Colors.RESET}")
        elif content_type == "subdir":
            print(f"{indent}  - {Colors.GREY}{item}/{Colors.RESET}")
        elif content_type == "subsummary":
            print(f"{indent}  {item}")
        elif content_type == "error":
            print(f"{indent}- {item}")
