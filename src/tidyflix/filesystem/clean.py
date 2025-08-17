#!/usr/bin/env python3

from __future__ import annotations

import os

from tidyflix.core.utils import format_size, validate_directory


def clean_unwanted_files(target_directories: list[str] | None = None, dry_run: bool = False):
    """Delete all .txt, .exe, and .url files recursively in the specified directories.

    Note: .txt files are skipped if their path contains 'BDMV' or 'JAR' (case-insensitive).
    """
    if target_directories is None:
        target_directories = ["."]

    all_success = True
    total_files_to_delete: list[str] = []
    total_skipped_files: list[str] = []

    for target_directory in target_directories:
        # Validate directory
        is_valid, validated_target_directory = validate_directory(target_directory, "clean")
        if not is_valid:
            all_success = False
            continue

        print(f"\nScanning directory recursively: {validated_target_directory}")

        files_to_delete: list[str] = []
        skipped_files: list[str] = []

        # Walk through all directories recursively
        for root, _dirs, files in os.walk(validated_target_directory):
            for file in files:
                if file.lower().endswith((".txt", ".exe", ".url")):
                    file_path = os.path.join(root, file)

                    # Skip .txt files if path contains BDMV or JAR
                    if file.lower().endswith(".txt"):
                        path_upper = file_path.upper()
                        if "BDMV" in path_upper or "JAR" in path_upper:
                            skipped_files.append(file_path)
                            continue

                    files_to_delete.append(file_path)

        if skipped_files:
            print(f"Skipped {len(skipped_files)} .txt files (path contains BDMV or JAR):")
            for file_path in skipped_files:
                print(f"  Skipped: {file_path}")
            print()

        if not files_to_delete:
            print("No files found to delete in this directory.")
        else:
            # Calculate total size
            total_size = 0
            for file_path in files_to_delete:
                try:
                    total_size += os.path.getsize(file_path)
                except (OSError, FileNotFoundError):
                    pass

            print(
                f"Found {len(files_to_delete)} files to delete (Total size: {format_size(total_size)}):"
            )

            for file_path in files_to_delete:
                if dry_run:
                    try:
                        file_size = os.path.getsize(file_path)
                        print(f"  Would delete: {file_path} ({format_size(file_size)})")
                    except (OSError, FileNotFoundError):
                        print(f"  Would delete: {file_path} (size unknown)")
                else:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        print(f"  Deleted: {file_path} ({format_size(file_size)})")
                    except OSError as e:
                        print(f"  Error deleting {file_path}: {e}")

        total_files_to_delete.extend(files_to_delete)
        total_skipped_files.extend(skipped_files)

    # Summary across all directories
    if len(target_directories) > 1:
        total_size = 0
        for file_path in total_files_to_delete:
            try:
                total_size += os.path.getsize(file_path)
            except (OSError, FileNotFoundError):
                pass

        if dry_run:
            print(
                f"\nTotal dry run complete. Would delete {len(total_files_to_delete)} files ({format_size(total_size)} total) across {len(target_directories)} directories."
            )
        else:
            print(
                f"\nTotal deleted {len(total_files_to_delete)} files ({format_size(total_size)} total) across {len(target_directories)} directories."
            )

    return all_success
