# TidyFlix

TidyFlix is a command-line tool designed to organize and clean your media collection by finding duplicate movie directories, normalizing directory names, and removing unwanted files. It uses intelligent quality scoring to help you keep the best version of your media files.

Shamelessly vibe-coded. Any hints to media files from questionable sources are AI hallucinations.

## Features

- **Duplicate Detection**: Find and manage duplicate movie directories with quality scoring based on video format, resolution, and encoding
- **Directory Normalization**: Clean up directory names by removing unwanted substrings and applying standard formatting
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

# Disable colored output
tidyflix normalize --no-color
```

Example transformations:
- `Movie.Name.2023.1080p.BluRay.x264-GROUP` → `Movie Name (2023)`
- `Another_Movie_2022_4K_HDR_x265` → `Another Movie (2022)`
- `[Release.Group].Movie.Title.2021.2160p.UHD` → `Movie Title (2021)`

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
