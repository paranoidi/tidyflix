"""
File operations and management functions.

This module handles file copying, subtitle management,
and video file operations.
"""

import os
import shutil

from tidyflix.analysis.subtitle_analyzer import (
    get_subtitle_files_by_language,
    is_media_file,
)
from tidyflix.core.models import Colors


def get_main_video_file(directory: str) -> str | None:
    """Find the largest video file in the directory."""
    largest_video = None
    largest_size = 0

    try:
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            if os.path.isfile(item_path) and is_media_file(item):
                try:
                    size = os.path.getsize(item_path)
                    if size > largest_size:
                        largest_size = size
                        largest_video = item
                except OSError:
                    continue
    except (PermissionError, OSError):
        pass

    return largest_video


def copy_additional_subtitles(kept_directory: str, directories_to_delete: list[str]) -> bool:
    """Copy additional subtitles from directories being deleted to the kept directory."""
    kept_files = get_subtitle_files_by_language(kept_directory)
    kept_languages = set(kept_files.keys())

    # Collect available subtitles from directories being deleted
    available_files: dict[
        str, list[tuple[str, str, str, bool]]
    ] = {}  # language -> list of (source_path, relative_path, filename, is_root)

    for delete_dir in directories_to_delete:
        delete_files = get_subtitle_files_by_language(delete_dir)

        for lang, files in delete_files.items():
            if lang not in available_files:
                available_files[lang] = []

            # Prefer files from root directory over nested ones
            for source_path, relative_path, filename in files:
                available_files[lang].append(
                    (source_path, relative_path, filename, "/" not in relative_path)
                )

    # Sort by preference (root directory first)
    for lang in available_files:
        available_files[lang].sort(key=lambda x: x[3], reverse=True)  # pyright: ignore[reportUnknownLambdaType]

    # Determine which languages to copy
    languages_to_copy: set[str] = set()

    if "generic" in kept_languages:
        # If kept directory has generic subtitle, only copy explicit languages
        languages_to_copy = (
            set(available_files.keys()) - {"generic"} - (kept_languages - {"generic"})
        )
    else:
        # If kept directory has no generic subtitle, copy any additional languages
        languages_to_copy = set(available_files.keys()) - kept_languages

    if not languages_to_copy:
        return False

    # Show what will be copied
    print(f"\n{Colors.GREEN}Additional subtitles found:{Colors.RESET}")

    for lang in sorted(languages_to_copy):
        if lang in available_files:
            files_for_lang = available_files[lang]

            if lang == "generic":
                print(
                    f"  GENERIC ({len(files_for_lang)} file{'s' if len(files_for_lang) > 1 else ''}):"
                )
            else:
                print(
                    f"  {lang.upper()} ({len(files_for_lang)} file{'s' if len(files_for_lang) > 1 else ''}):"
                )

            for source_path, _relative_path, original_filename, _is_root in files_for_lang:
                # Find which directory this file comes from
                source_dir = None
                for delete_dir in directories_to_delete:
                    if source_path.startswith(delete_dir):
                        source_dir = delete_dir
                        break

                if source_dir:
                    print(f"    - {original_filename} (from {source_dir})")
                else:
                    print(f"    - {original_filename}")

    print(f"\nWould copy to: {kept_directory}")
    copy_confirm = input("Copy additional subtitles to kept directory? [Y/n]: ").strip().lower()

    if copy_confirm in ["n", "no"]:
        return False

    # Get the main video file for naming reference
    main_video = get_main_video_file(kept_directory)
    video_base_name = os.path.splitext(main_video)[0] if main_video else "movie"

    copied_count = 0

    print("Copying subtitles...")
    for lang in sorted(languages_to_copy):
        if lang in available_files:
            files_for_lang = available_files[lang]

            for _i, (source_path, _relative_path, original_filename, _is_root) in enumerate(
                files_for_lang
            ):
                source_ext = os.path.splitext(original_filename)[1]

                # Determine target filename
                if len(files_for_lang) == 1 and lang != "generic":
                    # Single file for this language - can rename to match video
                    target_filename = f"{video_base_name}.{lang}{source_ext}"
                elif len(files_for_lang) == 1 and lang == "generic":
                    # Single generic file - can rename to match video
                    target_filename = f"{video_base_name}{source_ext}"
                else:
                    # Multiple files for same language - preserve original names
                    target_filename = original_filename

                target_path = os.path.join(kept_directory, target_filename)

                # Avoid overwriting existing files
                counter = 1
                base_target_path = target_path
                while os.path.exists(target_path):
                    name_part = os.path.splitext(base_target_path)[0]
                    ext_part = os.path.splitext(base_target_path)[1]
                    target_path = f"{name_part}_{counter}{ext_part}"
                    counter += 1

                try:
                    shutil.copy2(source_path, target_path)
                    final_filename = os.path.basename(target_path)
                    print(f"  Copied: {final_filename}")
                    copied_count += 1
                except Exception as e:
                    print(f"  Error copying {original_filename}: {e}")

    if copied_count > 0:
        print(f"Successfully copied {copied_count} subtitle file(s)")

    return copied_count > 0
