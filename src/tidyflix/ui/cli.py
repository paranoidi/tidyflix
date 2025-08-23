"""
Command line interface and argument parsing.

This module handles command line argument parsing,
validation, and initial setup for all subcommands.
"""

import argparse
import os
import sys
from dataclasses import dataclass

from tidyflix.core.models import Colors
from tidyflix.filesystem.clean import clean_unwanted_files
from tidyflix.operations.deletion import show_deletion_confirmation
from tidyflix.operations.filenames import normalize_filenames
from tidyflix.operations.normalize import normalize_directories
from tidyflix.operations.organize import organize_media_files
from tidyflix.operations.verify import verify_directories_have_media
from tidyflix.processing.duplicate_detector import discover_duplicates
from tidyflix.ui.interactive import process_with_background_scanning


def should_use_colors() -> bool:
    """Determine if colors should be used based on terminal support."""
    # Check for NO_COLOR environment variable first (https://no-color.org/)
    if os.environ.get("NO_COLOR"):
        return False

    # Check for FORCE_COLOR environment variable
    if os.environ.get("FORCE_COLOR"):
        return True

    # For piping to tools like less -R, we want to preserve colors
    # So we'll be more permissive and only disable in specific cases

    # Check TERM environment variable for known incompatible terminals
    term = os.environ.get("TERM", "").lower()
    if term in ["dumb", "unknown"]:
        return False

    # Default to using colors - let the user disable with --no-color if needed
    return True


@dataclass
class BaseCommandArgs:
    """Base arguments common to all commands."""

    directories: list[str]
    no_color: bool = False


@dataclass
class DuplicateArgs(BaseCommandArgs):
    """Arguments for duplicate detection command."""

    languages: list[str] | None = None


@dataclass
class NormalizeArgs(BaseCommandArgs):
    """Arguments for normalize command."""

    dry_run: bool = False
    explain: bool = False


@dataclass
class CleanArgs(BaseCommandArgs):
    """Arguments for clean command."""

    dry_run: bool = False


@dataclass
class OrganizeArgs(BaseCommandArgs):
    """Arguments for organize command."""

    dry_run: bool = False


@dataclass
class VerifyArgs(BaseCommandArgs):
    """Arguments for verify command."""

    delete: bool = False


@dataclass
class FilenamesArgs(BaseCommandArgs):
    """Arguments for filenames command."""

    dry_run: bool = False


def _validate_and_setup_common(args: BaseCommandArgs) -> list[str]:
    """Common validation and setup for all commands."""
    # Initialize color system
    if args.no_color or not should_use_colors():
        Colors.disable()

    # Validate directories
    target_dirs: list[str] = []
    for directory in args.directories:
        if not os.path.isdir(directory):
            print(f"Error: '{directory}' is not a valid directory")
            sys.exit(1)
        target_dirs.append(directory)

    return target_dirs


def parse_duplicate_arguments() -> DuplicateArgs:
    """Parse command line arguments for duplicate detection."""
    parser = argparse.ArgumentParser(
        description="Find and manage duplicate movie directories with quality scoring.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Process current directory
  %(prog)s /movies /movies-4k        # Process multiple directories
  %(prog)s -l EN                     # Show only English subtitles
  %(prog)s -l EN,FR /movies          # Show only English and French subtitles
  %(prog)s --languages EN,FR /movies # Alternative syntax for multiple languages
        """,
    )

    parser.add_argument(
        "directories",
        nargs="*",
        default=["."],
        help="Directories to scan for duplicates (default: current directory)",
    )

    parser.add_argument(
        "-l",
        "--languages",
        metavar="LANG",
        help="Comma-separated list of language codes to show in subtitle lists (e.g., EN,FR,ES)",
    )

    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    args = parser.parse_args()

    # Parse language filter
    language_filter = None
    if args.languages:
        # Handle comma-separated languages
        if "," in args.languages:
            language_filter = [lang.strip().upper() for lang in args.languages.split(",")]
        else:
            language_filter = [args.languages.upper()]

    return DuplicateArgs(
        directories=args.directories, no_color=args.no_color, languages=language_filter
    )


def parse_normalize_arguments() -> NormalizeArgs:
    """Parse command line arguments for normalize command."""
    parser = argparse.ArgumentParser(
        description="Normalize directory names by removing unwanted substrings and normalizing formatting.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                         # Normalize directories in current directory
  %(prog)s /movies                 # Normalize directories in specified path
  %(prog)s /movies /movies-4k      # Normalize directories in multiple paths
  %(prog)s --dry-run               # Preview changes without applying them
  %(prog)s -e                      # Show detailed cleaning steps (with colors)
  %(prog)s --no-color              # Disable colored output
        """,
    )

    parser.add_argument(
        "directories",
        nargs="*",
        default=["."],
        help="Directories to normalize (default: current directory)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without actually doing it",
    )

    parser.add_argument(
        "-e",
        "--explain",
        action="store_true",
        help="Show detailed steps of how each operation is performed",
    )

    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    args = parser.parse_args()

    return NormalizeArgs(
        directories=args.directories,
        no_color=args.no_color,
        dry_run=args.dry_run,
        explain=args.explain,
    )


def main_duplicate():
    """CLI entry point for duplicate detection command."""
    args = parse_duplicate_arguments()
    target_dirs = _validate_and_setup_common(args)

    # Display processing info
    if len(target_dirs) == 1 and target_dirs[0] == ".":
        abs_target_dir = os.path.abspath(".")
        print(f"{Colors.CYAN}Processing directory: {abs_target_dir}{Colors.RESET}")
    else:
        print(f"{Colors.CYAN}Processing directories: {', '.join(target_dirs)}{Colors.RESET}")

    if args.languages:
        print(f"{Colors.BOLD_BLUE}Language filter: {', '.join(args.languages)}{Colors.RESET}")

    # Execute business logic
    duplicate_groups_dict = discover_duplicates(target_dirs)

    if not duplicate_groups_dict:
        print(
            f"\n{Colors.GREEN}No duplicates found. All directories appear to be unique.{Colors.RESET}"
        )
        return

    to_delete = process_with_background_scanning(duplicate_groups_dict, args.languages)
    show_deletion_confirmation(to_delete)


def main_normalize():
    """CLI entry point for normalize command."""
    args = parse_normalize_arguments()
    target_dirs = _validate_and_setup_common(args)

    success = normalize_directories(
        target_directories=target_dirs, dry_run=args.dry_run, explain=args.explain
    )
    if not success:
        sys.exit(1)


def parse_clean_arguments() -> CleanArgs:
    """Parse command line arguments for clean command."""
    parser = argparse.ArgumentParser(
        description="Clean unwanted files (.txt, .exe, and .url) from directories recursively.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                         # Clean files in current directory
  %(prog)s /movies                 # Clean files in specified path
  %(prog)s /movies /movies-4k      # Clean files in multiple paths
  %(prog)s --dry-run               # Preview file deletions without deleting
  %(prog)s --no-color              # Disable colored output
        """,
    )

    parser.add_argument(
        "directories",
        nargs="*",
        default=["."],
        help="Directories to clean (default: current directory)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without actually doing it",
    )

    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    args = parser.parse_args()

    return CleanArgs(directories=args.directories, no_color=args.no_color, dry_run=args.dry_run)


def main_clean():
    """CLI entry point for clean command."""
    args = parse_clean_arguments()
    target_dirs = _validate_and_setup_common(args)

    success = clean_unwanted_files(target_directories=target_dirs, dry_run=args.dry_run)
    if not success:
        sys.exit(1)


def parse_organize_arguments() -> OrganizeArgs:
    """Parse command line arguments for organize command."""
    parser = argparse.ArgumentParser(
        description="Organize media files by moving them into subdirectories based on filename.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                         # Organize files in current directory
  %(prog)s /movies                 # Organize files in specified path
  %(prog)s /movies /movies-4k      # Organize files in multiple paths
  %(prog)s --dry-run               # Preview changes without applying them
  %(prog)s --no-color              # Disable colored output
        """,
    )

    parser.add_argument(
        "directories",
        nargs="*",
        default=["."],
        help="Directories to organize (default: current directory)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without actually doing it",
    )

    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    args = parser.parse_args()

    return OrganizeArgs(directories=args.directories, no_color=args.no_color, dry_run=args.dry_run)


def main_organize():
    """CLI entry point for organize command."""
    args = parse_organize_arguments()
    target_dirs = _validate_and_setup_common(args)

    success = organize_media_files(target_directories=target_dirs, dry_run=args.dry_run)
    if not success:
        sys.exit(1)


def parse_verify_arguments() -> VerifyArgs:
    """Parse command line arguments for verify command."""
    parser = argparse.ArgumentParser(
        description="Verify that each subdirectory contains at least one media file recursively.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                         # Verify subdirectories in current directory
  %(prog)s /movies                 # Verify subdirectories in specified path
  %(prog)s /movies /movies-4k      # Verify subdirectories in multiple paths
  %(prog)s --delete                # Delete directories without media files
  %(prog)s --no-color              # Disable colored output
        """,
    )

    parser.add_argument(
        "directories",
        nargs="*",
        default=["."],
        help="Directories to verify (default: current directory)",
    )

    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete directories that don't contain media files",
    )

    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    args = parser.parse_args()

    return VerifyArgs(directories=args.directories, no_color=args.no_color, delete=args.delete)


def main_verify():
    """CLI entry point for verify command."""
    args = parse_verify_arguments()
    target_dirs = _validate_and_setup_common(args)

    success = verify_directories_have_media(target_directories=target_dirs, delete=args.delete)
    if not success:
        sys.exit(1)


def parse_filenames_arguments() -> FilenamesArgs:
    """Parse command line arguments for filenames command."""
    parser = argparse.ArgumentParser(
        description="Rename main media files to match their parent directory names.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                         # Rename files in current directory
  %(prog)s /movies                 # Rename files in specified path
  %(prog)s /movies /movies-4k      # Rename files in multiple paths
  %(prog)s --dry-run               # Preview changes without applying them
  %(prog)s --no-color              # Disable colored output
        """,
    )

    parser.add_argument(
        "directories",
        nargs="*",
        default=["."],
        help="Directories to process (default: current directory)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without actually doing it",
    )

    parser.add_argument("--no-color", action="store_true", help="Disable colored output")

    args = parser.parse_args()

    return FilenamesArgs(directories=args.directories, no_color=args.no_color, dry_run=args.dry_run)


def main_filenames():
    """CLI entry point for filenames command."""
    args = parse_filenames_arguments()
    target_dirs = _validate_and_setup_common(args)

    success = normalize_filenames(target_directories=target_dirs, dry_run=args.dry_run)
    if not success:
        sys.exit(1)
