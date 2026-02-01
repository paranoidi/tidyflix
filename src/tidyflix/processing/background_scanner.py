"""
Background scanning and processing functions.

This module handles multithreaded background scanning of directories
and produces ready duplicate groups for processing.
"""

from __future__ import annotations

import queue
import threading
from collections.abc import Callable

from tidyflix.core.models import DirectoryInfo, DuplicateGroup
from tidyflix.filesystem.scanner import scan_directory_info
from tidyflix.processing.duplicate_detector import parse_prefix


class BackgroundScanner:
    """Handles background scanning of directories and produces ready duplicate groups."""

    def __init__(
        self,
        directories_by_prefix: dict[str, list[DirectoryInfo]],
        ready_queue: queue.Queue[DuplicateGroup | None],
        progress_callback: Callable[[int, int], None] | None = None,
        language_filter: list[str] | None = None,
    ):
        self.directories_by_prefix: dict[str, list[DirectoryInfo]] = directories_by_prefix
        self.ready_queue: queue.Queue[DuplicateGroup | None] = ready_queue
        self.progress_callback: Callable[[int, int], None] | None = progress_callback
        self.language_filter: list[str] | None = language_filter
        self.scanned_count: int = 0
        self.total_count: int = sum(len(dirs) for dirs in directories_by_prefix.values())  # pyright: ignore[reportUnknownLambdaType]
        self.running: bool = True
        self.thread: threading.Thread | None = None

    def start(self):
        """Start the background scanning thread."""
        self.thread = threading.Thread(target=self._scan_worker, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the background scanning."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def get_progress(self) -> tuple[int, int]:
        """Get current scanning progress."""
        return self.scanned_count, self.total_count

    def _scan_worker(self):
        """Background worker that scans directories and produces ready groups."""
        for prefix, dir_list in self.directories_by_prefix.items():
            if not self.running:
                break

            # Scan all directories in this group
            scanned_dirs: list[DirectoryInfo] = []
            for dir_info in dir_list:
                if not self.running:
                    break

                # Scan this directory
                scanned_dir = scan_directory_info(dir_info, self.language_filter)
                scanned_dirs.append(scanned_dir)
                self.scanned_count += 1

                # Notify progress callback if provided
                if self.progress_callback:
                    self.progress_callback(self.scanned_count, self.total_count)

            if not self.running:
                break

            # Create and queue the complete duplicate group
            if scanned_dirs:
                # Initial sort by size (largest first) - will be re-sorted by score later
                scanned_dirs.sort(key=lambda x: x.size_bytes or 0, reverse=True)  # pyright: ignore[reportUnknownLambdaType]

                # Extract original prefix from first directory for display
                # The prefix parameter is normalized (lowercase), but we want the original capitalization
                original_prefix = parse_prefix(scanned_dirs[0].name)
                # Fallback to normalized prefix if parse_prefix returns None (shouldn't happen)
                display_prefix = original_prefix if original_prefix else prefix

                group = DuplicateGroup(display_prefix, scanned_dirs)
                group.calculate_size_info()

                # Put the ready group in the queue
                self.ready_queue.put(group)

        # Signal completion
        self.ready_queue.put(None)
