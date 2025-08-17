"""
Main entry point for TidyFlix with subcommand support.

This module handles duplicate detection, directory normalization, and file cleaning functionality.
"""

import sys

from tidyflix.ui.cli import main_duplicate


def run_duplicate_detection():
    """Run the duplicate detection process."""
    main_duplicate()


def run_normalize():
    """Run the directory normalization process."""
    from tidyflix.ui.cli import main_normalize

    # Remove the 'normalize' subcommand from argv so normalize's argparse works normally
    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    try:
        main_normalize()
    finally:
        sys.argv = original_argv


def run_clean():
    """Run the file cleaning process."""
    from tidyflix.ui.cli import main_clean

    # Remove the 'clean' subcommand from argv so clean's argparse works normally
    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    try:
        main_clean()
    finally:
        sys.argv = original_argv


def run_organize():
    """Run the media file organization process."""
    from tidyflix.ui.cli import main_organize

    # Remove the 'organize' subcommand from argv so organize's argparse works normally
    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    try:
        main_organize()
    finally:
        sys.argv = original_argv


def run_verify():
    """Run the directory verification process."""
    from tidyflix.ui.cli import main_verify

    # Remove the 'verify' subcommand from argv so verify's argparse works normally
    original_argv = sys.argv[:]
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    try:
        main_verify()
    finally:
        sys.argv = original_argv


def show_main_help():
    """Show the main help message with subcommand information."""
    print("""TidyFlix - Tidy your media collection by removing duplicates and cleaning up your files.

Usage:
  tidyflix [options] [directories...]  # Find and manage duplicate movie directories
  tidyflix normalize [options]         # Normalize directory names to standard format
  tidyflix clean [options]             # Clean unwanted files (.txt, .exe, and .url)
  tidyflix organize [options]          # Organize media files into subdirectories
  tidyflix verify [options]            # Verify subdirectories contain media files

Duplicate Detection (default):
  Find and manage duplicate movie directories with quality scoring.

  Arguments:
    directories               # Directories to scan for duplicates (default: current directory)

  Options:
    -h, --help               # Show this help message and exit
    -l, --languages LANG     # Comma-separated list of language codes to show in subtitle lists
                               (e.g. EN,FR,ES)

  Examples:
    tidyflix                          # Process current directory
    tidyflix /movies /movies-4k       # Process multiple directories
    tidyflix -l EN                    # Show only English subtitles
    tidyflix -l EN,FR /movies         # Show English and French subtitles

Directory Normalization:
  Normalize directory names by removing unwanted substrings and applying standard formatting.

  Usage:
    tidyflix normalize [options] [directories...]

  Arguments:
    directories             # Directories to normalize (default: current directory)

  Options:
    --dry-run               # Show what would be renamed without actually doing it
    -e, --explain           # Show detailed steps of how each directory name is cleaned
    --no-color              # Disable colored output
    -h, --help              # Show help for normalize subcommand

  Examples:
    tidyflix normalize                     # Normalize directories in current directory
    tidyflix normalize /movies             # Normalize directories in specified path
    tidyflix normalize /movies /movies-4k  # Normalize directories in multiple paths
    tidyflix normalize --dry-run           # Preview changes without applying them
    tidyflix normalize -e                  # Show detailed cleaning steps

File Cleaning:
  Clean unwanted files (.txt, .exe, and .url) from directories recursively.

  Usage:
    tidyflix clean [options] [directories...]

  Arguments:
    directories             # Directories to clean (default: current directory)

  Options:
    --dry-run               # Show what would be deleted without actually doing it
    --no-color              # Disable colored output
    -h, --help              # Show help for clean subcommand

  Examples:
    tidyflix clean                     # Clean files in current directory
    tidyflix clean /movies             # Clean files in specified path
    tidyflix clean /movies /movies-4k  # Clean files in multiple paths
    tidyflix clean --dry-run           # Preview file deletions without deleting

Media File Organization:
  Organize media files by moving them into subdirectories based on their filenames.

  Usage:
    tidyflix organize [options] [directories...]

  Arguments:
    directories             # Directories to organize (default: current directory)

  Options:
    --dry-run               # Show what would be organized without actually doing it
    --no-color              # Disable colored output
    -h, --help              # Show help for organize subcommand

  Examples:
    tidyflix organize                     # Organize files in current directory
    tidyflix organize /movies             # Organize files in specified path
    tidyflix organize /movies /movies-4k  # Organize files in multiple paths
    tidyflix organize --dry-run           # Preview organization without doing it

Directory Verification:
  Verify that each subdirectory contains at least one media file recursively.

  Usage:
    tidyflix verify [options] [directories...]

  Arguments:
    directories             # Directories to verify (default: current directory)

  Options:
    --delete                # Delete directories that don't contain media files
    --no-color              # Disable colored output
    -h, --help              # Show help for verify subcommand

  Examples:
    tidyflix verify                     # Verify subdirectories in current directory
    tidyflix verify /movies             # Verify subdirectories in specified path
    tidyflix verify /movies /movies-4k  # Verify subdirectories in multiple paths
    tidyflix verify --delete            # Delete directories without media files

For more help on a specific subcommand:
  tidyflix normalize --help
  tidyflix clean --help
  tidyflix organize --help
  tidyflix verify --help""")


def main():
    """Main entry point with subcommand support."""
    # Check if first argument is a subcommand
    if len(sys.argv) > 1 and sys.argv[1] == "normalize":
        run_normalize()
    elif len(sys.argv) > 1 and sys.argv[1] == "clean":
        run_clean()
    elif len(sys.argv) > 1 and sys.argv[1] == "organize":
        run_organize()
    elif len(sys.argv) > 1 and sys.argv[1] == "verify":
        run_verify()
    elif len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        # Show main help with subcommand information
        show_main_help()
    elif len(sys.argv) > 1 and sys.argv[1] == "help":
        # Handle 'tidyflix help <subcommand>' syntax
        if len(sys.argv) > 2 and sys.argv[2] == "normalize":
            sys.argv = ["tidyflix", "normalize", "--help"]
            run_normalize()
        elif len(sys.argv) > 2 and sys.argv[2] == "clean":
            sys.argv = ["tidyflix", "clean", "--help"]
            run_clean()
        elif len(sys.argv) > 2 and sys.argv[2] == "organize":
            sys.argv = ["tidyflix", "organize", "--help"]
            run_organize()
        elif len(sys.argv) > 2 and sys.argv[2] == "verify":
            sys.argv = ["tidyflix", "verify", "--help"]
            run_verify()
        else:
            show_main_help()
    else:
        # Default behavior - run duplicate detection
        run_duplicate_detection()


if __name__ == "__main__":
    main()
