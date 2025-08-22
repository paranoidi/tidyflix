"""
Configuration constants and settings for the duplicate movie detector.

This module centralizes all configuration values, file extensions, and scoring parameters.
"""

# File extensions
MEDIA_EXTENSIONS = (".mkv", ".mp4", ".avi", ".mov")
SUBTITLE_EXTENSIONS = {
    ".srt",
    ".sub",
    ".ass",
    ".ssa",
    ".vtt",
    ".idx",
    ".sup",
    ".smi",
    ".rt",
    ".sbv",
}

# Scoring configuration
MAX_SIZE_SCORE = 25  # Maximum points for size comparison

# Encoding efficiency multipliers for adjusted size calculation
# Higher multiplier = better scoring for same file size
ENCODING_MULTIPLIERS = {
    "AV1": 2.5,  # Most efficient, highest multiplier
    "H265": 2.0,  # More efficient than H264
    "H264": 1.0,  # Baseline efficiency
}

# Tag scoring weights - points awarded for each quality indicator
TAG_SCORES = {
    # Video encodings
    "AV1": 12,
    "H265": 10,
    "H264": 5,
    # Resolutions
    "2160p": 15,
    "4K": 15,
    "1080p": 8,
    "720p": 3,
    # Quality features
    "10bit": 5,
    "HDR10": 12,
    "HDR": 8,
    "DV": 15,  # Dolby Vision
    "IMAX": 7,
    "REPACK": 2,
    "3D": 0,
}

# Color assignments for tags
from tidyflix.core.models import Colors

TAG_COLORS = {
    # High quality indicators - Green
    "AV1": Colors.GREEN,
    "H265": Colors.GREEN,
    "2160p": Colors.GREEN,
    "4K": Colors.GREEN,
    "10bit": Colors.GREEN,
    "HDR10": Colors.GREEN,
    "HDR": Colors.GREEN,
    "DV": Colors.GREEN,
    "IMAX": Colors.GREEN,
    "REPACK": Colors.GREEN,
    # Medium quality indicators - Yellow
    "H264": Colors.YELLOW,
    "1080p": Colors.YELLOW,
    # Lower quality indicators - Red
    "720p": Colors.RED,
    "3D": Colors.RED,
}

# Default values
DEFAULT_DIRECTORY = "."
DEFAULT_INDENT = "   "
