"""
Interactive user interface functions.

This module handles user interaction, group processing,
and the main interactive workflow.
"""

import queue
import sys
import threading

from tidyflix.analysis.video_analyzer import calculate_relative_size_scores
from tidyflix.core.models import Colors, DirectoryInfo, DuplicateGroup
from tidyflix.filesystem.file_operations import copy_additional_subtitles
from tidyflix.processing.background_scanner import BackgroundScanner
from tidyflix.ui.display import get_size_color, list_directory_contents_cached


def add_others_to_delete_list(
    directories: list[DirectoryInfo], keep_index: int, to_delete: list[str]
):
    """Add all directories except the selected one to the delete list."""
    kept_directory = directories[keep_index]
    directories_to_delete: list[str] = []

    # Collect directories that will be deleted
    for j, dir_info in enumerate(directories):
        if j != keep_index:
            directories_to_delete.append(dir_info.abs_path)

    # Check for and copy additional subtitles
    if directories_to_delete:
        copy_additional_subtitles(kept_directory.abs_path, directories_to_delete)

    # Add to the main delete list
    to_delete.extend(directories_to_delete)


def process_duplicate_group(
    duplicate_group: DuplicateGroup,
    to_delete: list[str],
    current_group: int | None = None,
    total_groups: int | None = None,
) -> bool:
    """Process a single group of duplicate directories using pre-scanned data."""
    print(f"\n=== {Colors.CYAN}{duplicate_group.prefix}{Colors.RESET} ===")
    print()

    directories = duplicate_group.directories

    # Calculate relative size scores within this group
    calculate_relative_size_scores(directories)

    # Sort by score (highest first) - this puts the best quality option first
    directories.sort(key=lambda x: x.video_score if x.video_score is not None else 0, reverse=True)

    # Calculate baseline score (lowest score in the group) for delta calculation
    baseline_score = min(
        (dir_info.video_score for dir_info in directories if dir_info.video_score is not None),
        default=0,
    )

    # Display options
    for i, dir_info in enumerate(directories, 1):
        color = get_size_color(
            dir_info,
            duplicate_group.min_size_dir if duplicate_group.min_size_dir is not None else dir_info,
            duplicate_group.max_size_dir if duplicate_group.max_size_dir is not None else dir_info,
        )

        # Display delta score if available and positive
        score_display = ""
        if dir_info.video_score is not None and dir_info.video_score > baseline_score:
            delta_score = dir_info.video_score - baseline_score
            score_display = f" {Colors.CYAN}(+{delta_score}){Colors.RESET}"

        print(
            f"{color}{i}.{Colors.RESET} {dir_info.name:40s} {color}{dir_info.size_mb:10.2f} MB{Colors.RESET}{dir_info.video_tags}{score_display}"
        )

        # Display source directory on a new line if processing multiple directories
        if len(set(d.source_dir for d in directories)) > 1:
            print(f"   {Colors.GREY}Source: {dir_info.source_dir}{Colors.RESET}")

        # Display subtitle summary on a new line if available
        if dir_info.subtitle_summary:
            print(f"   {Colors.BLUE}Subs: {dir_info.subtitle_summary}{Colors.RESET}")

        list_directory_contents_cached(dir_info.contents or [])

    # Handle user input
    while True:
        try:
            # Create progress prefix if progress information is available
            progress_prefix = (
                f"[{current_group}/{total_groups}] " if current_group and total_groups else ""
            )
            choice = input(
                f"\n{progress_prefix}Select item to KEEP (1-{len(directories)}), press Enter for 1, 's' to skip, 'd' when done, 'a' to delete all, or 'q' to quit: "
            ).strip()

            if not choice:  # Default to selecting 1
                add_others_to_delete_list(directories, 0, to_delete)
                return False

            if choice.lower() == "s":  # Skip this group
                return False

            if choice.lower() == "d":  # Done - stop processing
                return True

            if choice.lower() == "a":  # Delete all directories in this group
                for dir_info in directories:
                    to_delete.append(dir_info.abs_path)
                print(f"Marked all {len(directories)} directories for deletion")
                return False

            if choice.lower() == "q":  # Quit immediately
                quit_confirm = input("Are you sure you want to quit? [Y/n]: ").strip().lower()
                if quit_confirm in ["n", "no"]:
                    continue  # Go back to the selection prompt
                print("Quitting without deletion.")
                sys.exit(0)

            choice_num = int(choice)
            if 1 <= choice_num <= len(directories):
                add_others_to_delete_list(directories, choice_num - 1, to_delete)
                return False
            else:
                print(f"Please enter a number between 1 and {len(directories)}")
        except ValueError:
            print(
                "Please enter a valid number, press Enter for 1, 's' to skip, 'd' when done, 'a' to delete all, or 'q' to quit"
            )


def process_with_background_scanning(
    duplicate_groups_dict: dict[str, list[DirectoryInfo]], language_filter: list[str] | None = None
) -> list[str]:
    """Process duplicates with background scanning and early interactive start."""

    # Set up the queue for ready groups
    ready_queue: queue.Queue[DuplicateGroup | None] = queue.Queue()

    # Progress tracking
    progress_lock = threading.Lock()
    last_progress_update = [0]  # Use list to modify from callback

    def progress_callback(scanned: int, total: int):  # pyright: ignore[reportUnusedParameter]
        with progress_lock:
            last_progress_update[0] = scanned

    # Start background scanner
    print(f"\n{Colors.CYAN}Phase 2: Background analysis started...{Colors.RESET}")
    scanner = BackgroundScanner(
        duplicate_groups_dict, ready_queue, progress_callback, language_filter
    )
    scanner.start()

    # Wait for first groups to be ready
    ready_groups: list[DuplicateGroup] = []
    processed_groups = 0
    to_delete: list[str] = []
    total_groups = len(duplicate_groups_dict)
    started_interactive = False

    print("Waiting for initial analysis to complete...")

    # Process groups as they become ready
    while True:
        try:
            # Wait for next ready group (with timeout to update progress)
            group = ready_queue.get(timeout=1.0)

            if group is None:  # Scanning completed
                break

            ready_groups.append(group)

            # Start interactive processing when we have groups ready
            # Initial start: wait for at least 3 groups or 1 group for small collections
            # After initial start: process groups immediately as they become ready
            should_start = (
                not started_interactive
                and (
                    len(ready_groups) >= min(3, total_groups)  # Initial batch: have enough groups
                    or len(ready_groups) >= 1  # Or at least 1 group for immediate start
                )
            ) or (
                started_interactive and ready_groups  # After initial start: process immediately
            )

            if should_start:
                if not started_interactive:
                    started_interactive = True
                    # Clear the progress line
                    print(f"\r{' ' * 60}\r", end="")

                # Sort groups alphabetically
                ready_groups.sort(key=lambda g: g.prefix)  # pyright: ignore[reportUnknownLambdaType]

                # Process the ready groups
                for group in ready_groups:
                    processed_groups += 1

                    # Show progress with background status
                    scanned, total = scanner.get_progress()
                    if scanned < total:
                        print(
                            f"\n{Colors.GREEN}Background scan progress {scanned}/{total}{Colors.RESET}"
                        )

                    should_stop = process_duplicate_group(
                        group, to_delete, processed_groups, total_groups
                    )
                    if should_stop:
                        scanner.stop()
                        return to_delete

                ready_groups = []  # Clear processed groups

        except queue.Empty:
            # Update progress display while waiting
            if not started_interactive:
                scanned, total = scanner.get_progress()
                if scanned < total:
                    ready_count = len(ready_groups)
                    print(
                        f"\rBackground analysis: {scanned}/{total} directories ({ready_count} duplicates ready)...",
                        end="",
                        flush=True,
                    )

    # Process any remaining groups
    if ready_groups:
        # Clear any remaining progress output
        print(f"\r{' ' * 60}\r", end="")

        ready_groups.sort(key=lambda g: g.prefix)  # pyright: ignore[reportUnknownLambdaType]
        for group in ready_groups:
            processed_groups += 1
            print(
                f"\n{Colors.GREEN}Processing duplicate {processed_groups}/{total_groups} (final batch){Colors.RESET}"
            )
            should_stop = process_duplicate_group(group, to_delete, processed_groups, total_groups)
            if should_stop:
                break

    scanner.stop()
    return to_delete
