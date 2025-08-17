"""
Subtitle analysis and language detection functions.

This module handles subtitle file detection, language extraction,
embedded subtitle analysis, and subtitle formatting.
"""

import os

from pymediainfo import MediaInfo

from tidyflix.core.config import MEDIA_EXTENSIONS, SUBTITLE_EXTENSIONS
from tidyflix.core.models import Colors


def is_subtitle_file(filename: str) -> bool:
    """Check if a file is a subtitle file based on its extension."""
    return any(filename.lower().endswith(ext) for ext in SUBTITLE_EXTENSIONS)


def is_media_file(filename: str) -> bool:
    """Check if a file is a media file."""
    return filename.lower().endswith(MEDIA_EXTENSIONS)


def extract_language_from_filename(filename: str) -> str:
    """Extract language code from subtitle filename."""
    base_name = os.path.splitext(filename)[0]
    parts = base_name.split(".")
    if len(parts) > 1 and len(parts[-1]) == 2:  # likely language code
        lang = parts[-1].upper()
        return format_subtitle_entry(lang, "ext")
    return format_subtitle_entry("EXT")


def format_subtitle_entry(lang: str, format_name: str | None = None) -> str:
    """Format a subtitle entry with proper colors: language in blue, format in grey."""
    if format_name:
        return f"{Colors.BOLD_BLUE}{lang}{Colors.GREY}({format_name}){Colors.RESET}"
    else:
        return f"{Colors.BOLD_BLUE}{lang}{Colors.RESET}"


def get_embedded_subtitles(file_path: str) -> set[str]:
    """Extract embedded subtitle information from media files."""
    subtitles: set[str] = set()
    try:
        media_info = MediaInfo.parse(file_path)
        for track in media_info.tracks:  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
            if track.track_type == "Text":  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                lang = (track.language or "UNK").upper()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                format_name = track.format or "UNK"  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                # Omit UTF-8 as it's just encoding, not format
                if format_name == "UTF-8":
                    subtitles.add(format_subtitle_entry(lang))  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
                else:
                    subtitles.add(format_subtitle_entry(lang, format_name))  # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType]
    except Exception:
        pass
    return subtitles


def get_directory_subtitles(directory_path: str, language_filter: list[str] | None = None) -> str:
    """Get combined list of all subtitles in a directory (embedded + external)."""
    all_subtitles: set[str] = set()

    try:
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path):
                if is_subtitle_file(item):
                    all_subtitles.add(extract_language_from_filename(item))
                elif is_media_file(item):
                    all_subtitles.update(get_embedded_subtitles(item_path))
    except Exception:
        return ""

    if all_subtitles:
        # Filter subtitles by language if filter is provided
        if language_filter:
            filtered_subtitles: set[str] = set()
            for subtitle in all_subtitles:
                # Extract language code from formatted subtitle (e.g., "EN(ext)" -> "EN")
                # Check if any part of the subtitle contains one of our filtered languages
                subtitle_upper = subtitle.upper()
                for lang in language_filter:
                    if lang in subtitle_upper:
                        filtered_subtitles.add(subtitle)
                        break
            all_subtitles = filtered_subtitles

        if all_subtitles:
            return f"{', '.join(sorted(all_subtitles))}"

    return ""


def find_subtitle_files(directory: str, base_path: str = "") -> list[tuple[str, str]]:
    """Recursively find all subtitle files in a directory."""
    subtitle_files: list[tuple[str, str]] = []
    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            relative_path = os.path.join(base_path, item) if base_path else item

            if os.path.isfile(item_path) and is_subtitle_file(item):
                subtitle_files.append((item_path, relative_path))
            elif os.path.isdir(item_path):
                subtitle_files.extend(find_subtitle_files(item_path, relative_path))
    except (PermissionError, OSError):
        pass
    return subtitle_files


def extract_language_code(filename: str) -> str | None:
    """Extract 2-letter language code from filename."""
    base_name = os.path.splitext(filename)[0]
    parts = base_name.split(".")
    for part in reversed(parts):
        if len(part) == 2 and part.isalpha():
            return part.lower()
    return None


def get_subtitle_files_by_language(directory: str) -> dict[str, list[tuple[str, str, str]]]:
    """Get subtitle files organized by language, preserving multiple files per language.
    Returns dict: language -> list of (source_path, relative_path, filename)"""
    language_files: dict[str, list[tuple[str, str, str]]] = {}

    subtitle_files = find_subtitle_files(directory)
    for source_path, relative_path in subtitle_files:
        filename = os.path.basename(relative_path)
        lang = extract_language_code(filename)

        # Use 'generic' for files without language codes
        lang_key = lang if lang else "generic"

        if lang_key not in language_files:
            language_files[lang_key] = []

        language_files[lang_key].append((source_path, relative_path, filename))

    return language_files
