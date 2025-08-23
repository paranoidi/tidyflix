"""
Filename normalization functionality.

This module provides functionality to rename main media files to match their
parent directory names while preserving file extensions.
"""

from __future__ import annotations

from pathlib import Path

from tidyflix.core.config import SUBTITLE_EXTENSIONS
from tidyflix.core.models import Colors
from tidyflix.core.utils import highlight_changes
from tidyflix.filesystem.file_operations import get_main_video_file


def _get_subtitle_files(directory_path: Path, media_filename: str) -> list[Path]:
    """
    Find subtitle files that should be renamed along with the media file.

    Returns list of subtitle files that can be safely renamed.
    For .srt files, only returns them if there's exactly one (to avoid conflicts).
    """
    # Extensions we want to handle for renaming
    target_extensions = {".srt", ".idx", ".sub", ".srr"}

    media_stem = Path(media_filename).stem.lower()
    subtitle_files = []
    srt_files = []

    # Find all subtitle files in the directory
    for file_path in directory_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in SUBTITLE_EXTENSIONS:
            if file_path.suffix.lower() in target_extensions:
                if file_path.suffix.lower() == ".srt":
                    srt_files.append(file_path)
                else:
                    subtitle_files.append(file_path)

    # For .srt files, only include if there's exactly one
    if len(srt_files) == 1:
        subtitle_files.extend(srt_files)

    # Filter to only files that appear to belong to the media file
    # (either exact match or similar naming pattern)
    relevant_subtitles = []
    for sub_file in subtitle_files:
        sub_stem = sub_file.stem.lower()
        # Check if subtitle filename starts with or closely matches media filename
        if (
            sub_stem.startswith(media_stem)
            or media_stem.startswith(sub_stem)
            or _files_appear_related(media_filename, sub_file.name)
        ):
            relevant_subtitles.append(sub_file)

    return relevant_subtitles


def _extract_language_code(subtitle_filename: str, media_stem: str) -> str | None:
    """
    Extract language code from subtitle filename by removing media stem prefix.

    Args:
        subtitle_filename: Full subtitle filename (e.g., "messy_movie_name.en.srt")
        media_stem: Media filename without extension (e.g., "messy_movie_name")

    Returns:
        Language code if found (e.g., "en"), None if subtitle doesn't match media file
    """
    # Remove extension from subtitle filename
    sub_stem = Path(subtitle_filename).stem

    # Check if subtitle stem starts with media stem (case insensitive)
    if not sub_stem.lower().startswith(media_stem.lower()):
        return None

    # Remove media stem prefix to get the remainder
    remainder = sub_stem[len(media_stem) :]

    # Remove leading dots and spaces
    lang_code = remainder.lstrip(". ")

    # If we have something left, that's our language code
    return lang_code if lang_code else None


def _files_appear_related(media_filename: str, subtitle_filename: str) -> bool:
    """
    Check if a subtitle file appears to be related to the media file.
    """
    media_stem = Path(media_filename).stem

    # Try to extract language code - if successful, files are related
    return _extract_language_code(subtitle_filename, media_stem) is not None


def _generate_subtitle_name(
    original_subtitle_name: str, old_media_name: str, new_media_name: str
) -> str:
    """
    Generate new subtitle filename based on the media file rename.
    Preserves language codes and other suffixes using dynamic extraction.
    """
    old_media_stem = Path(old_media_name).stem
    new_media_stem = Path(new_media_name).stem
    subtitle_ext = Path(original_subtitle_name).suffix

    # Extract language code from the original subtitle filename
    lang_code = _extract_language_code(original_subtitle_name, old_media_stem)

    if lang_code:
        # Construct new name with preserved language code
        return f"{new_media_stem}.{lang_code}{subtitle_ext}"
    else:
        # Fallback: just use new media name with original extension
        return f"{new_media_stem}{subtitle_ext}"


def normalize_filenames(target_directories: list[str], dry_run: bool = False) -> bool:
    """
    Normalize media filenames to match their parent directory names.

    For each subdirectory, finds the main media file and renames it to match
    the directory name while preserving the original extension.

    Args:
        target_directories: List of directory paths to process
        dry_run: If True, show what would be done without actually doing it

    Returns:
        True if successful, False if any errors occurred
    """
    success = True
    total_processed = 0

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

        # Find all subdirectories
        subdirectories = []
        for item in dir_path.iterdir():
            if item.is_dir():
                subdirectories.append(item)

        if not subdirectories:
            print(f"  No subdirectories found in {dir_path}")
            continue

        print(f"  Found {len(subdirectories)} subdirectory(ies)")

        # Process each subdirectory
        for subdir in subdirectories:
            processed = _normalize_single_directory(subdir, dry_run)
            if processed:
                total_processed += 1

    # Summary
    if dry_run:
        print(
            f"\n{Colors.CYAN}Dry run complete. {total_processed} file(s) would be renamed.{Colors.RESET}"
        )
    else:
        print(
            f"\n{Colors.GREEN}Filename normalization complete. {total_processed} file(s) renamed successfully.{Colors.RESET}"
        )

    return success


def _normalize_single_directory(subdir_path: Path, dry_run: bool) -> bool:
    """
    Normalize the main media file and related subtitle files in a single subdirectory.

    Args:
        subdir_path: Path to the subdirectory
        dry_run: If True, show what would be done without actually doing it

    Returns:
        True if file was renamed (or would be renamed in dry run), False otherwise
    """
    # Find the main media file
    main_video_filename = get_main_video_file(str(subdir_path))

    if not main_video_filename:
        return False

    main_video_path = subdir_path / main_video_filename

    # Get the directory name and file extension
    directory_name = subdir_path.name
    file_extension = main_video_path.suffix

    # Generate the new filename
    new_filename = f"{directory_name}{file_extension}"
    new_file_path = subdir_path / new_filename

    # Check if rename is needed
    if main_video_filename == new_filename:
        return False

    # Check if destination already exists
    if new_file_path.exists() and new_file_path != main_video_path:
        print(
            f"  {Colors.RED}Skipping {directory_name} - destination file already exists: {new_filename}{Colors.RESET}"
        )
        return False

    # Find subtitle files that should be renamed
    subtitle_files = _get_subtitle_files(subdir_path, main_video_filename)
    subtitle_renames = []

    for sub_file in subtitle_files:
        new_sub_name = _generate_subtitle_name(sub_file.name, main_video_filename, new_filename)
        new_sub_path = subdir_path / new_sub_name

        # Skip if destination already exists (avoid conflicts)
        if new_sub_path.exists() and new_sub_path != sub_file:
            continue

        subtitle_renames.append((sub_file, new_sub_path, new_sub_name))

    if dry_run:
        print(f"{Colors.BOLD_WHITE}{directory_name}{Colors.RESET}")
        before_highlighted, after_highlighted = highlight_changes(main_video_filename, new_filename)
        print(f"    Before: {before_highlighted}")
        print(f"    After : {after_highlighted}")

        # Show subtitle renames
        for sub_file, _, new_sub_name in subtitle_renames:
            if (sub_file.name == new_sub_name):
                continue
            sub_before_highlighted, sub_after_highlighted = highlight_changes(
                sub_file.name, new_sub_name
            )
            print(f"    {Colors.BOLD_BLUE}Before:{Colors.RESET} {sub_before_highlighted}")
            print(f"    {Colors.BOLD_BLUE}After :{Colors.RESET} {sub_after_highlighted}")

        return True

    try:
        # Perform the media file rename
        main_video_path.rename(new_file_path)
        print(
            f"  {Colors.GREEN}Renamed:{Colors.RESET} {main_video_filename} -> {new_filename} in {directory_name}"
        )

        # Rename subtitle files
        for sub_file, new_sub_path, new_sub_name in subtitle_renames:
            try:
                sub_file.rename(new_sub_path)
                print(f"  {Colors.GREEN}Renamed:{Colors.RESET} {sub_file.name} -> {new_sub_name}")
            except OSError as e:
                print(
                    f"  {Colors.YELLOW}Warning:{Colors.RESET} Could not rename subtitle {sub_file.name} - {e}"
                )

        return True

    except OSError as e:
        print(
            f"  {Colors.RED}FAILED:{Colors.RESET} Could not rename {main_video_filename} in {directory_name} - {e}"
        )
        return False
