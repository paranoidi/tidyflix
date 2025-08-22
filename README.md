# TidyFlix

TidyFlix is a command-line tool designed to organize and clean your media collection by finding duplicate movie directories, normalizing directory names, and removing unwanted files. It uses intelligent quality scoring to help you keep the best version of your media files.

Shamelessly vibe-coded. Any hints to media files from questionable sources are AI hallucinations.

## Features

- **Duplicate Detection**: Find and manage duplicate movie directories with quality scoring based on video format, resolution, and encoding
- **Directory Normalization**: Clean up directory names by removing unwanted substrings and applying standard formatting
- **Directory Verification**: Make sure directories contain at least one media file.
- **Organize Files**: Move media files into subdirectories with same name.
- **File Cleaning**: Remove unwanted files (`.txt`, `.exe`, `.url`) from your media directories with intelligence to leave them in BDMV.
- **Interactive Processing**: User-friendly interface with colored output and confirmation prompts
- **Background Scanning**: Efficient processing with background analysis for large collections
- **Quality Scoring**: Intelligent scoring system that considers video codecs, resolution, HDR, and other quality factors

## Installation

Install from source:

```bash
git clone https://github.com/paranoidi/tidyflix.git
cd tidyflix
uv sync
```

## Usage Examples

### Finding and Managing Duplicates (Default Command)

**Recommendation**: Run `tidyflix normalize` before duplicate detection to ensure directory names are standardized, which improves duplicate matching accuracy.

The main functionality of TidyFlix is finding duplicate movie directories and helping you decide which ones to keep:

```bash
# Process current directory
tidyflix

# Process specific directories
tidyflix /movies /movies-4k

# Show only English subtitles in analysis
tidyflix -l EN /movies

# Show multiple languages (English and French)
tidyflix -l EN,FR /movies
```

The duplicate detection process:
1. Scans directories to find movies with the same title and year
2. Analyzes video quality (codec, resolution, HDR, etc.)
3. Provides an interactive interface to choose which versions to keep
4. Shows detailed information about file sizes, video formats, and subtitles

### Directory Normalization

Clean up messy directory names by removing unwanted text and standardizing format:

```bash
# Normalize current directory
tidyflix normalize

# Normalize specific directories
tidyflix normalize /movies /movies-4k

# Preview changes without applying them
tidyflix normalize --dry-run

# Show detailed explanation of each change
tidyflix normalize --explain

# Automatically accept deletions (non-interactive mode)
tidyflix normalize -y

# Disable colored output
tidyflix normalize --no-color
```

Example transformations:
- `Movie.Name.2023.1080p.BluRay.x264-GROUP` → `Movie Name (2023)`
- `Another_Movie_2022_4K_HDR_x265` → `Another Movie (2022)`
- `[Release.Group].Movie.Title.2021.2160p.UHD` → `Movie Title (2021)`

#### Intelligent Conflict Resolution

When normalizing results in a naming conflict (two directories would have the same name), TidyFlix uses intelligent logic to determine which directory to keep:

1. **Media Priority**: If only one directory contains media files, the empty directory is automatically deleted
2. **Size Comparison**: If both directories have media files (or both are empty), the smaller directory is deleted
3. **Clear Analysis**: Shows detailed reasoning before taking action

Example conflict resolution:
```
Directory conflict detected!
Source:      'Movie.Title.2023.1080p.x264' -> (1.2 GB, 15 files, 2 subdirectories)
Destination: 'Movie Title (2023)' -> (890.5 MB, 8 files, 1 subdirectories)

Intelligent deletion analysis:
  Source has media files: True
  Destination has media files: False
  → Deleting destination (no media files)
```

### File Cleaning

Remove unwanted files that often come with downloads:

```bash
# Clean current directory
tidyflix clean

# Clean specific directories
tidyflix clean /movies /movies-4k

# Preview what would be deleted
tidyflix clean --dry-run

# Disable colored output
tidyflix clean --no-color
```

Removes:
- `.txt` files (except those in BDMV or JAR directories)
- `.exe` files
- `.url` files

### Directory Verification

Verify that subdirectories contain at least one media file recursively:

```bash
# Verify current directory
tidyflix verify

# Verify specific directories
tidyflix verify /movies /movies-4k

# Delete directories without media files
tidyflix verify --delete

# Disable colored output
tidyflix verify --no-color
```

This command helps identify empty directories that may have been left behind after cleaning or moving files.

### File Organization

Move media files into subdirectories based on their filenames:

```bash
# Organize current directory
tidyflix organize

# Organize specific directories
tidyflix organize /movies /movies-4k

# Preview changes without applying them
tidyflix organize --dry-run

# Disable colored output
tidyflix organize --no-color
```

This command takes loose media files and creates subdirectories with the same name (minus extension), then moves the files into those directories. Useful for organizing downloads that come as individual files rather than in folders.

## Command Reference

### Main Command (Duplicate Detection)
```bash
tidyflix [options] [directories...]
```

**Options:**
- `-l, --languages LANG`: Filter subtitle display to specific languages (e.g., `EN,FR,ES`)
- `-h, --help`: Show help message

### Normalize Subcommand
```bash
tidyflix normalize [options] [directories...]
```

**Options:**
- `--dry-run`: Preview changes without applying them
- `-e, --explain`: Show detailed steps for each transformation
- `-y, --yes`: Automatically accept deletions without prompting (for non-interactive use)
- `--no-color`: Disable colored output
- `-h, --help`: Show help for normalize command

### Clean Subcommand
```bash
tidyflix clean [options] [directories...]
```

**Options:**
- `--dry-run`: Preview deletions without removing files
- `--no-color`: Disable colored output
- `-h, --help`: Show help for clean command

### Verify Subcommand
```bash
tidyflix verify [options] [directories...]
```

**Options:**
- `--delete`: Delete directories that don't contain media files
- `--no-color`: Disable colored output
- `-h, --help`: Show help for verify command

### Organize Subcommand
```bash
tidyflix organize [options] [directories...]
```

**Options:**
- `--dry-run`: Preview changes without applying them
- `--no-color`: Disable colored output
- `-h, --help`: Show help for organize command

## Quality Scoring System

TidyFlix uses an intelligent scoring system to help identify the best quality versions:

- **Video Codecs**: H.265/HEVC scores higher than H.264/AVC
- **Resolution**: 4K/2160p > 1440p > 1080p > 720p > 480p
- **HDR Support**: HDR10, Dolby Vision, and other HDR formats add bonus points
- **Audio Quality**: Lossless audio formats score higher
- **File Size**: Considers encoding efficiency (smaller files with better codecs score higher)

## Requirements

- Python 3.11 or higher
- `pymediainfo` for video analysis

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests on [GitHub](https://github.com/paranoidi/tidyflix).
