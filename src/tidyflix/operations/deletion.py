"""
File deletion operations and confirmation handling.

This module handles the deletion confirmation process
and actual file system deletion operations.
"""

import os
import shutil

from tidyflix.core.models import Colors
from tidyflix.core.utils import get_directory_size as get_dir_size


def show_deletion_confirmation(to_delete: list[str]):
    """Show deletion confirmation and handle the deletion process."""
    if not to_delete:
        print("\nNo directories selected for deletion.")
        return

    print(f"\n=== DIRECTORIES TO DELETE ({len(to_delete)} items) ===")
    total_bytes = 0
    for d in to_delete:
        size_bytes = get_dir_size(d)
        size_mb = size_bytes / (1024 * 1024)
        total_bytes += size_bytes
        print(f"{os.path.basename(d):40s} {size_mb:10.2f} MB")

    total_mb = total_bytes / (1024 * 1024)
    print(f"\n{Colors.GREEN}Total space to free: {total_mb:.2f} MB{Colors.RESET}")

    while True:
        confirm = input("\nConfirm deletion? (y/n): ").strip().lower()
        if confirm in ["yes", "y"]:
            print("\nDeleting directories...")
            for d in to_delete:
                try:
                    shutil.rmtree(d)
                    print(f"Deleted: {os.path.basename(d)}")
                except Exception as e:
                    print(f"Error deleting {os.path.basename(d)}: {e}")
            print(f"\nDeletion complete. {len(to_delete)} directories processed.")
            break
        elif confirm in ["n", "no"]:
            print("Deletion cancelled.")
            break
        else:
            print("Please enter valid selection.")
