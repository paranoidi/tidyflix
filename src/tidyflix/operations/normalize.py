#!/usr/bin/env python3

from __future__ import annotations

import difflib
import os
import re
import shutil
import tempfile
from abc import ABC, ABCMeta, abstractmethod

from typing_extensions import override

from tidyflix.core.models import Colors
from tidyflix.core.utils import (
    get_directory_info,
    get_directory_size,
    validate_directory,
)
from tidyflix.operations.verify import _has_media_files_recursive


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


class NormalizeMeta(ABCMeta):
    """Metaclass that automatically registers normalizer classes."""

    registry: list[type[Normalize]] = []

    def __new__(  # pyright: ignore[reportGeneralTypeIssues,reportUnknownParameterType]
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, any],  # pyright: ignore[reportGeneralTypeIssues,reportUnknownParameterType]
        **kwargs: any,  # pyright: ignore[reportGeneralTypeIssues,reportUnknownParameterType]
    ) -> type:
        new_class = super().__new__(cls, name, bases, namespace, **kwargs)  # pyright: ignore[reportUnknownArgumentType,reportGeneralTypeIssues]
        # Only register concrete normalizer classes (not the base Normalize class)
        if name != "Normalize" and bases:
            cls.registry.append(new_class)  # pyright: ignore[reportArgumentType]
        return new_class


class Normalize(ABC, metaclass=NormalizeMeta):
    """Base class for all string normalizers."""

    @abstractmethod
    def normalize(self, text: str) -> str:
        """Normalize the input text and return the normalized version."""
        pass

    @classmethod
    def normalize_string(cls, text: str, max_iterations: int = 10, explain: bool = False) -> str:
        """
        Apply all registered normalizers iteratively until no further changes occur.

        Args:
            text: The string to normalize
            max_iterations: Maximum number of iterations to prevent infinite loops
            explain: If True, log changes made by each normalizer

        Returns:
            The normalized string
        """
        current_text = text

        for iteration in range(max_iterations):
            previous_text = current_text
            iteration_changes = False

            # Apply all registered normalizers
            for normalizer_class in NormalizeMeta.registry:
                normalizer = normalizer_class()
                before_normalize = current_text
                current_text = normalizer.normalize(current_text)

                if explain and before_normalize != current_text:
                    orig_highlighted, new_highlighted = highlight_changes(
                        before_normalize, current_text
                    )
                    print(f"  {normalizer_class.__name__}:")
                    print(f"    Before: '{orig_highlighted}'")
                    print(f"    After:  '{new_highlighted}'")
                    iteration_changes = True

            # If no changes were made, we're done
            if current_text == previous_text:
                break
            elif explain and iteration_changes:
                print(f"  End of iteration {iteration + 1}: '{current_text}'")

        if explain and text != current_text:
            print(f"Final result: '{current_text}'")

        return current_text


class SubstringRemovalNormalizer(Normalize):
    """Removes unwanted substrings from text."""

    SUBSTRINGS_TO_REMOVE: list[str] = [
        "www.UIndex.org    -    ",
        "[TGx]",
        "[EtHD]",
        "[rarbg]",
        "DDLValley.COOL",
        "[www.YYeTs.net]",
        "[norar]",
        "[no-rar]",
        "Rarbg.Com-",
        "[ www.torrentday.com ]",
    ]

    @override
    def normalize(self, text: str) -> str:
        result = text
        for substring in self.SUBSTRINGS_TO_REMOVE:
            pattern = re.compile(re.escape(substring), re.IGNORECASE)
            result = pattern.sub(".", result)
        return result


class SpaceReplacementNormalizer(Normalize):
    """Replaces spaces, underscores, and commas with dots."""

    @override
    def normalize(self, text: str) -> str:
        result = text
        result = result.replace(" ", ".")
        result = result.replace("_", ".")
        result = result.replace(",", ".")
        return result


class DotCollapseNormalizer(Normalize):
    """Collapses multiple consecutive dots into a single dot."""

    @override
    def normalize(self, text: str) -> str:
        return re.sub(r"\.{2,}", ".", text)


class ColonRemovalNormalizer(Normalize):
    """Removes various types of colons and colon-like characters."""

    @override
    def normalize(self, text: str) -> str:
        return re.sub(r"[:\uA789\u2236\uFF1A\u02D0]", "", text)


class SpecialDotPatternNormalizer(Normalize):
    """Replaces patterns like .-. .+. .~. .–. with single dot."""

    @override
    def normalize(self, text: str) -> str:
        return re.sub(r"\.[\-\+\~\u2013]\.", ".", text)


class EndBracketReplacementNormalizer(Normalize):
    """Replaces end bracket patterns with dash format."""

    @override
    def normalize(self, text: str) -> str:
        m = re.match(r"^(.*?)(\[[^\]]+\])$", text)
        if m:
            before, bracketed = m.groups()
            if not re.search(r"-\w+$", before):
                return before + "-" + bracketed[1:-1]
        return text


class ParensBracketsBracesNormalizer(Normalize):
    """Replaces parentheses, brackets, and braces with dots."""

    @override
    def normalize(self, text: str) -> str:
        # replace with dot so that (2019)(720p) does not become 2019720p
        return re.sub(r"[\(\)\[\]\{\}]", ".", text)


class DashDotNormalizer(Normalize):
    """Cleans up dash-dot patterns."""

    @override
    def normalize(self, text: str) -> str:
        result = text
        # Replace -. with single dot
        result = re.sub(r"\-\.", ".", result)
        # Replace .- with single dot
        result = re.sub(r"\.\-", ".", result)
        return result


class TrailingCrapNormalizer(Normalize):
    """Removes trailing non-alphanumeric characters."""

    @override
    def normalize(self, text: str) -> str:
        return re.sub(r"[^A-Za-z0-9]+$", "", text)


class TrailingDotNormalizer(Normalize):
    """Removes trailing dots."""

    @override
    def normalize(self, text: str) -> str:
        return text.rstrip(".")


class TitleCaseNormalizer(Normalize):
    """Capitalizes words (separated by dots) up to the first numeric word.

    Preserves words that are 4 letters or less and in uppercase.
    """

    @override
    def normalize(self, text: str) -> str:
        if not text:
            return text

        parts = text.split(".")

        # Find the year part (if any) to determine which parts to check
        year_index = None
        for i, part in enumerate(parts):
            if re.search(r"\d{4}", part):
                year_index = i
                break

        # Check capitalization pattern of words before the year
        parts_to_check = parts[:year_index] if year_index is not None else parts
        capitalized_count = 0
        non_empty_parts = 0

        for part in parts_to_check:
            if part:  # Skip empty parts
                non_empty_parts += 1
                if part[0].isupper():
                    capitalized_count += 1

        # Skip normalization only if SOME (but not all) words are capitalized
        # If all words are capitalized, we still want to apply normalization
        if non_empty_parts > 0 and 0 < capitalized_count < non_empty_parts:
            # Found mixed capitalization, don't apply normalization
            return text

        # No capitalized words found, proceed with normalization
        result_parts: list[str] = []

        for part in parts:
            # Check if this part is 4 digits (year)
            if re.search(r"\d{4}", part):
                # Found year, add it as-is and stop capitalizing
                result_parts.append(part)
                # Add remaining parts unchanged
                remaining_index = parts.index(part) + 1
                result_parts.extend(parts[remaining_index:])
                break
            else:
                # Preserve words that are 4 letters or less and already uppercase
                if len(part) <= 4 and part.isupper() and part.isalpha():
                    result_parts.append(part)
                else:
                    # Capitalize this word
                    result_parts.append(part.capitalize())

        return ".".join(result_parts)


class TermCapitalizer(Normalize):
    """Normalizes capitalization of specific terms to their preferred form."""

    TERM_CAPITALIZATIONS: list[tuple[str, str]] = [
        ("720p", "720p"),
        ("1080p", "1080p"),
        ("2160p", "2160p"),
        ("4k", "4K"),
        ("limited", "LIMITED"),
        ("extended", "EXTENDED"),
        ("unrated", "UNRATED"),
        ("uncut", "UNCUT"),
        ("proper", "PROPER"),
        ("repack", "REPACK"),
        ("rerip", "RERIP"),
        ("multi", "MULTi"),
        ("bluray", "BluRay"),
        ("dvd", "DVD"),
        ("hdtv", "HDTV"),
        ("webrip", "WebRip"),
        ("webdl", "WebDL"),
        ("bdrip", "BDRip"),
        ("dvdrip", "DVDRip"),
        ("hdcam", "HDCam"),
        ("hdrip", "HDRip"),
        ("xvid", "XviD"),
        ("divx", "DivX"),
        ("x264", "x264"),
        ("x265", "x265"),
        ("h264", "H264"),
        ("h265", "H265"),
        ("avc", "AVC"),
        ("hevc", "HEVC"),
        ("aac", "AAC"),
        ("ac3", "AC3"),
        ("dts", "DTS"),
        ("flac", "FLAC"),
        ("mp3", "MP3"),
        ("truehd", "TrueHD"),
        ("atmos", "Atmos"),
        ("dolby", "Dolby"),
        ("netflix", "Netflix"),
        ("hulu", "Hulu"),
        ("amazon", "Amazon"),
        ("disney", "Disney"),
        ("hbo", "HBO"),
        ("apple", "Apple"),
        ("paramount", "Paramount"),
        ("peacock", "Peacock"),
    ]

    @override
    def normalize(self, text: str) -> str:
        result = text
        # Split by dots to handle each part separately
        parts = result.split(".")

        for i, part in enumerate(parts):
            # Check each term capitalization pair
            for lowercase_term, preferred_cap in self.TERM_CAPITALIZATIONS:
                if part.lower() == lowercase_term.lower():
                    parts[i] = preferred_cap
                    break

        return ".".join(parts)


class TermMover(Normalize):
    """Moves specific terms after the year in the filename."""

    TERMS_TO_MOVE: list[str] = [
        "proper",
        "repack",
        "rerip",
        "limited",
        "extended",
        "unrated",
        "theatrical",
        "internal",
    ]

    @override
    def normalize(self, text: str) -> str:
        if not text:
            return text

        parts = text.split(".")

        # Find the year part
        year_index = None
        for i, part in enumerate(parts):
            if re.search(r"^\d{4}$", part):
                year_index = i
                break

        # If no year found, return original text
        if year_index is None:
            return text

        # Find terms to move (before year)
        terms_to_move = []
        indices_to_remove = []

        for i in range(year_index):
            part = parts[i]
            if part.lower() in [term.lower() for term in self.TERMS_TO_MOVE]:
                terms_to_move.append(part)
                indices_to_remove.append(i)

        # If no terms to move, return original text
        if not terms_to_move:
            return text

        # Remove the terms from their original positions (reverse order to maintain indices)
        for i in reversed(indices_to_remove):
            parts.pop(i)
            # Adjust year_index since we removed items before it
            year_index -= 1

        # Insert terms after the year
        for i, term in enumerate(terms_to_move):
            parts.insert(year_index + 1 + i, term)

        return ".".join(parts)


class LeadingDotNormalizer(Normalize):
    """Removes leading dots."""

    @override
    def normalize(self, text: str) -> str:
        return text.lstrip(".")


def is_case_insensitive_filesystem(directory: str) -> bool:
    """
    Check if the filesystem at the given directory is case-insensitive.

    Returns True if case-insensitive, False if case-sensitive.
    """
    try:
        # Create a temporary file with lowercase name
        with tempfile.NamedTemporaryFile(
            mode="w", dir=directory, prefix=".tidyflix_case_test_", suffix=".tmp", delete=False
        ) as temp_file:
            temp_lower = temp_file.name

        # Generate uppercase version of the same path
        dirname, basename = os.path.split(temp_lower)
        temp_upper = os.path.join(dirname, basename.upper())

        # Check if uppercase version exists (would indicate case-insensitive)
        case_insensitive = os.path.exists(temp_upper)

        # Clean up
        try:
            os.unlink(temp_lower)
        except FileNotFoundError:
            pass

        return case_insensitive

    except (OSError, PermissionError):
        # If we can't test, assume case-sensitive for safety
        return False


def determine_directory_to_delete(source_path: str, destination_path: str) -> str:
    """
    Determine which directory to delete when there's a name conflict.

    Rules:
    1. If only one directory has media files, delete the one without media
    2. If both have media files, delete the smaller one (by total size)
    3. If neither has media files, delete the smaller one

    Args:
        source_path: Path to the source directory (being renamed)
        destination_path: Path to the existing destination directory

    Returns:
        Path to the directory that should be deleted
    """
    source_has_media = _has_media_files_recursive(source_path)
    dest_has_media = _has_media_files_recursive(destination_path)

    # If only one has media files, delete the one without media
    if source_has_media and not dest_has_media:
        return destination_path
    elif dest_has_media and not source_has_media:
        return source_path

    # Both have media files (or both don't), compare sizes
    source_size = get_directory_size(source_path)
    dest_size = get_directory_size(destination_path)

    # Delete the smaller directory
    if source_size <= dest_size:
        return source_path
    else:
        return destination_path


def check_case_only_rename_safety(old_path: str, new_path: str, directory: str) -> bool:
    """
    Check if a case-only rename is safe to perform.

    Returns True if safe to proceed, False if should abort.
    """
    # Check if the paths differ only by case
    if old_path.lower() != new_path.lower():
        return True  # Different paths - not a case-only change

    # Check if filesystem is case-insensitive
    if is_case_insensitive_filesystem(directory):
        return False  # Case-insensitive filesystem - unsafe

    return True  # Case-sensitive filesystem - safe


def normalize_directories(
    target_directories: list[str] | None = None,
    dry_run: bool = False,
    explain: bool = False,
    auto_accept: bool = False,
):
    """Normalize directory names by applying string normalization rules."""
    if target_directories is None:
        target_directories = ["."]

    print(f"Registered normalizers: {len(NormalizeMeta.registry)}")

    all_success = True

    for target_directory in target_directories:
        # Validate directory
        is_valid, validated_target_directory = validate_directory(target_directory, "normalize")
        if not is_valid:
            all_success = False
            continue

        print(f"\nProcessing directory: {validated_target_directory}")

        directories = [
            d
            for d in os.listdir(validated_target_directory)
            if os.path.isdir(os.path.join(validated_target_directory, d))
        ]

        for dir_name in directories:
            old_path = os.path.join(validated_target_directory, dir_name)
            new_dir_name = Normalize.normalize_string(dir_name, explain=explain)

            if dir_name == new_dir_name:
                continue

            new_path = os.path.join(validated_target_directory, new_dir_name)

            if dry_run:
                orig_highlighted, new_highlighted = highlight_changes(dir_name, new_dir_name)
                print(f"  Before: '{orig_highlighted}'")
                print(f"  After:  '{new_highlighted}'")
                continue

            # Check for conflicts
            if os.path.exists(new_path):
                # Check if this is a case-only change on unsafe filesystem
                is_safe = check_case_only_rename_safety(
                    old_path, new_path, validated_target_directory
                )
                if not is_safe:
                    print(f"\n❌ ERROR: Cannot safely rename '{dir_name}' to '{new_dir_name}'")
                    print(
                        "Reason: Case-insensitive filesystem detected (e.g., Samba/CIFS mount). Case-only renames are unsafe and may cause data loss."
                    )
                    all_success = False
                    continue

                if os.path.isdir(new_path):
                    print("\nDirectory conflict detected!")
                    print(f"Source:      '{dir_name}' -> ({get_directory_info(old_path)})")
                    print(f"Destination: '{new_dir_name}' -> ({get_directory_info(new_path)})")

                    # Determine which directory should be deleted based on media content and size
                    directory_to_delete = determine_directory_to_delete(old_path, new_path)

                    source_has_media = _has_media_files_recursive(old_path)
                    dest_has_media = _has_media_files_recursive(new_path)

                    # Explain the decision
                    print("\nIntelligent deletion analysis:")
                    print(f"  Source has media files: {source_has_media}")
                    print(f"  Destination has media files: {dest_has_media}")

                    if source_has_media != dest_has_media:
                        # One has media, one doesn't
                        if directory_to_delete == new_path:
                            print("  → Deleting destination (no media files)")
                        else:
                            print("  → Deleting source (no media files)")
                    else:
                        # Both have media or both don't - size comparison
                        source_size = get_directory_size(old_path)
                        dest_size = get_directory_size(new_path)
                        print(f"  Source size: {source_size:,} bytes")
                        print(f"  Destination size: {dest_size:,} bytes")
                        if directory_to_delete == new_path:
                            print("  → Deleting destination (smaller/equal size)")
                        else:
                            print("  → Deleting source (smaller/equal size)")

                    if auto_accept:
                        print(f"Auto-accepting deletion of: {directory_to_delete}")
                        response = "y"
                    else:
                        dir_to_delete_name = os.path.basename(directory_to_delete)
                        response = (
                            input(
                                f'Delete "{dir_to_delete_name}" as determined by analysis? [Y/n]: '
                            )
                            .strip()
                            .lower()
                        )

                    if response == "n":
                        print(f"Skipped: {old_path}")
                        continue

                    # Handle the deletion and rename logic
                    if directory_to_delete == new_path:
                        # Delete destination, then rename source
                        print(f"Deleting destination directory: {new_path}")
                        shutil.rmtree(new_path)
                        # Continue with normal rename below
                    else:
                        # Delete source, skip rename
                        print(f"Deleting source directory: {old_path}")
                        shutil.rmtree(old_path)
                        print(f"Kept existing destination: {new_path}")
                        continue
                else:
                    print(f"Error: Cannot rename {old_path} -> {new_path} (file exists)")
                    continue

            os.rename(old_path, new_path)
            orig_highlighted, new_highlighted = highlight_changes(dir_name, new_dir_name)
            print(f"  Before: '{orig_highlighted}'")
            print(f"  After:  '{new_highlighted}'")

    return all_success
