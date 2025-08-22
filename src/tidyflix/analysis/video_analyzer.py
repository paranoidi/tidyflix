"""
Video analysis and quality assessment functions.

This module handles video encoding detection, tag parsing, scoring,
and quality assessment for movie directories.
"""

import os
import re

from pymediainfo import MediaInfo

from tidyflix.core.config import ENCODING_MULTIPLIERS, MAX_SIZE_SCORE, TAG_COLORS, TAG_SCORES
from tidyflix.core.models import Colors, DirectoryInfo, Tag


def get_video_encoding_from_files(directory_path: str) -> str | None:
    """Use pymediainfo to detect video encoding from media files."""
    try:
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path) and _is_media_file_basic(item):
                try:
                    media_info = MediaInfo.parse(item_path)
                    for track in media_info.tracks:  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                        if track.track_type == "Video":  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                            codec = track.codec_id or track.format or ""  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
                            codec_lower = codec.lower()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]

                            # Check for AV1
                            if any(av1_id in codec_lower for av1_id in ["av01", "av1"]):
                                return "AV1"
                            # Check for H.265/HEVC
                            elif any(
                                h265_id in codec_lower
                                for h265_id in ["hevc", "h265", "x265", "hev1", "hvc1"]
                            ):
                                return "H265"
                            # Check for H.264/AVC
                            elif any(
                                h264_id in codec_lower
                                for h264_id in ["avc", "h264", "x264", "avc1"]
                            ):
                                return "H264"

                            # Only check the first video file found
                            break
                    # Only check the first media file found
                    break
                except Exception:
                    continue
    except Exception:
        pass
    return None


def _is_media_file_basic(filename: str) -> bool:
    """Basic check if a file is a media file - internal helper."""
    from tidyflix.core.config import MEDIA_EXTENSIONS

    return filename.lower().endswith(MEDIA_EXTENSIONS)


def parse_video_tags_with_score(
    directory_name: str, directory_path: str | None = None, size_mb: float = 0
) -> tuple[list[Tag], int]:
    """Parse video tags and return tag objects and total score."""
    tags: list[Tag] = []
    name_lower = directory_name.lower()
    encoding_detected = False

    # Check for video encoding (priority: AV1 > H265 > H264)
    # AV1 must be surrounded by space or dot
    if re.search(r"[\s\.]av1[\s\.]|^av1[\s\.]|[\s\.]av1$", name_lower):
        tags.append(Tag("AV1", TAG_COLORS["AV1"], score=TAG_SCORES["AV1"]))
        encoding_detected = True
    elif any(codec in name_lower for codec in ["h265", "x265", "h.265", "x.265"]):
        tags.append(Tag("H265", TAG_COLORS["H265"], score=TAG_SCORES["H265"]))
        encoding_detected = True
    elif any(codec in name_lower for codec in ["h264", "x264", "h.264", "x.264"]):
        tags.append(Tag("H264", TAG_COLORS["H264"], score=TAG_SCORES["H264"]))
        encoding_detected = True

    # If no encoding detected from filename and directory path provided, check media files
    if not encoding_detected and directory_path:
        detected_encoding = get_video_encoding_from_files(directory_path)
        if detected_encoding == "AV1":
            tags.append(Tag("AV1", TAG_COLORS["AV1"], score=TAG_SCORES["AV1"]))
        elif detected_encoding == "H265":
            tags.append(Tag("H265", TAG_COLORS["H265"], score=TAG_SCORES["H265"]))
        elif detected_encoding == "H264":
            tags.append(Tag("H264", TAG_COLORS["H264"], score=TAG_SCORES["H264"]))

    # Check for resolution (priority order: 2160p > 4K > 1080p > 720p)
    if "2160p" in name_lower:
        tags.append(Tag("2160p", TAG_COLORS["2160p"], score=TAG_SCORES["2160p"]))
    elif re.search(r"[\s\.]4k[\s\.]|^4k[\s\.]|[\s\.]4k$", name_lower):
        tags.append(Tag("4K", TAG_COLORS["4K"], score=TAG_SCORES["4K"]))
    elif "1080p" in name_lower:
        tags.append(Tag("1080p", TAG_COLORS["1080p"], score=TAG_SCORES["1080p"]))
    elif "720p" in name_lower:
        tags.append(Tag("720p", TAG_COLORS["720p"], score=TAG_SCORES["720p"]))

    # Check for bit depth
    if "10bit" in name_lower:
        tags.append(Tag("10bit", TAG_COLORS["10bit"], score=TAG_SCORES["10bit"]))

    # Check for HDR (HDR10 takes precedence over plain HDR)
    if "hdr10" in name_lower:
        tags.append(Tag("HDR10", TAG_COLORS["HDR10"], score=TAG_SCORES["HDR10"]))
    elif "hdr" in name_lower:
        tags.append(Tag("HDR", TAG_COLORS["HDR"], score=TAG_SCORES["HDR"]))

    # Check for DV (Dolby Vision) with regex requiring space or dot before and after
    if re.search(r"[\s\.]dv[\s\.]", name_lower):
        tags.append(Tag("DV", TAG_COLORS["DV"], score=TAG_SCORES["DV"]))

    # Check for IMAX
    if "imax" in name_lower:
        tags.append(Tag("IMAX", TAG_COLORS["IMAX"], score=TAG_SCORES["IMAX"]))

    # Check for REPACK
    if "repack" in name_lower:
        tags.append(Tag("REPACK", TAG_COLORS["REPACK"], score=TAG_SCORES["REPACK"]))

    # Check for 3D (must be surrounded by space or dot)
    if re.search(r"[\s\.]3d[\s\.]|^3d[\s\.]|[\s\.]3d$", name_lower):
        tags.append(Tag("3D", TAG_COLORS["3D"], score=TAG_SCORES["3D"]))

    # Calculate tag-based score
    tag_score = sum(tag.score for tag in tags)

    # Only calculate size score if size_mb > 0 (for backward compatibility)
    # Relative size scoring will be handled separately in calculate_relative_size_scores
    if size_mb > 0:
        # This is legacy mode - just return tag score for now
        # Size scoring will be calculated relatively later
        total_score = tag_score
    else:
        # Just tag score
        total_score = tag_score

    return tags, total_score


def calculate_adjusted_size(size_mb: float, tags: list[Tag]) -> float:
    """Calculate size adjusted for encoding efficiency."""
    if size_mb <= 0:
        return 0.0

    # Determine encoding type from tags and apply multiplier
    # AV1 > H265 > H264 efficiency (higher multiplier = better scoring for same size)
    encoding_multiplier = 1.0  # Default for H264 and unknown encodings
    for tag in tags:
        if tag.name == "AV1":
            encoding_multiplier = ENCODING_MULTIPLIERS["AV1"]
            break
        elif tag.name == "H265":
            encoding_multiplier = ENCODING_MULTIPLIERS["H265"]
            break
        elif tag.name == "H264":
            encoding_multiplier = ENCODING_MULTIPLIERS["H264"]
            break

    # For comparison: H265 file gets bigger adjusted size for scoring
    # This means H265 files are rewarded for their efficiency
    adjusted_size_mb = size_mb * encoding_multiplier

    return adjusted_size_mb


def calculate_relative_size_scores(
    directories: list[DirectoryInfo], max_size_score: int = MAX_SIZE_SCORE
) -> None:
    """Calculate relative size scores within a group of directories."""
    if not directories:
        return

    # Find the maximum adjusted size in the group
    max_adjusted_size = max(
        dir_info.adjusted_size_mb
        for dir_info in directories
        if dir_info.adjusted_size_mb is not None
    )

    if max_adjusted_size <= 0:
        return

    # Calculate relative scores based on the largest file in the group
    for dir_info in directories:
        if dir_info.adjusted_size_mb is not None and dir_info.adjusted_size_mb > 0:
            # Calculate proportional score (largest gets full points, others get proportional)
            ratio = dir_info.adjusted_size_mb / max_adjusted_size
            size_score = int(ratio * max_size_score)

            # Update the total video score by adding the size score
            # Remove any previous size scoring and add the new relative score
            if dir_info.video_score is not None:
                # Extract tag score (video_score currently includes old size scoring)
                # We need to recalculate from just the tags
                _, tag_score_only = parse_video_tags_with_score(
                    dir_info.name,
                    dir_info.abs_path,
                    size_mb=0,  # Don't include size in this calculation
                )
                dir_info.video_score = tag_score_only + size_score
            else:
                dir_info.video_score = size_score


def format_video_tags(tags: list[Tag]) -> str:
    """Format video tags for display."""
    if tags:
        return f"{Colors.RESET} [{', '.join(str(tag) for tag in tags)}]"
    return ""
