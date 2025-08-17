from __future__ import annotations

from tidyflix.operations.normalize import (
    ColonRemovalNormalizer,
    DashDotNormalizer,
    DotCollapseNormalizer,
    EndBracketReplacementNormalizer,
    LeadingDotNormalizer,
    Normalize,
    ParensBracketsBracesNormalizer,
    SpaceReplacementNormalizer,
    SpecialDotPatternNormalizer,
    SubstringRemovalNormalizer,
    TermCapitalizer,
    TitleCaseNormalizer,
    TrailingCrapNormalizer,
    TrailingDotNormalizer,
)


def test_substring_removal_normalizer():
    """Test SubstringRemovalNormalizer functionality."""
    normalizer = SubstringRemovalNormalizer()

    # Test replacement of specific substrings with dots
    assert normalizer.normalize("Movie[TGx]") == "Movie."
    assert normalizer.normalize("Movie[RARBG]") == "Movie."  # Case insensitive
    assert normalizer.normalize("Moviewww.UIndex.org    -    Title") == "Movie.Title"
    assert normalizer.normalize("Movie[EtHD]720p") == "Movie.720p"
    assert normalizer.normalize("Movie DDLValley.COOL Bluray") == "Movie . Bluray"
    assert normalizer.normalize("Movie[www.YYeTs.net]2021") == "Movie.2021"
    assert normalizer.normalize("Movie[norar]x264") == "Movie.x264"
    assert normalizer.normalize("Movie[no-rar]1080p") == "Movie.1080p"
    assert normalizer.normalize("Movie[ www.torrentday.com ]HD") == "Movie.HD"

    # Test multiple substrings
    assert normalizer.normalize("Movie[TGx][rarbg]") == "Movie.."

    # Test no change
    assert normalizer.normalize("Clean.Movie.Title") == "Clean.Movie.Title"


def test_space_replacement_normalizer():
    """Test SpaceReplacementNormalizer functionality."""
    normalizer = SpaceReplacementNormalizer()

    # Test space replacement
    assert normalizer.normalize("Movie Title 1999") == "Movie.Title.1999"

    # Test underscore replacement
    assert normalizer.normalize("Movie_Title_1999") == "Movie.Title.1999"

    # Test comma replacement
    assert normalizer.normalize("Movie,Title,1999") == "Movie.Title.1999"

    # Test mixed replacements
    assert normalizer.normalize("Movie Title_1999, 720p") == "Movie.Title.1999..720p"

    # Test no change
    assert normalizer.normalize("Movie.Title.1999") == "Movie.Title.1999"


def test_dot_collapse_normalizer():
    """Test DotCollapseNormalizer functionality."""
    normalizer = DotCollapseNormalizer()

    # Test collapsing multiple dots
    assert normalizer.normalize("Movie..Title...1999") == "Movie.Title.1999"
    assert normalizer.normalize("Movie....Title") == "Movie.Title"
    assert normalizer.normalize("Test.......File") == "Test.File"

    # Test no change
    assert normalizer.normalize("Movie.Title.1999") == "Movie.Title.1999"

    # Test single dots preserved
    assert normalizer.normalize("A.B.C") == "A.B.C"


def test_colon_removal_normalizer():
    """Test ColonRemovalNormalizer functionality."""
    normalizer = ColonRemovalNormalizer()

    # Test regular colon
    assert normalizer.normalize("Movie:Title") == "MovieTitle"

    # Test Unicode colons
    assert normalizer.normalize("Movie\ua789Title") == "MovieTitle"  # modifier letter colon
    assert normalizer.normalize("Movie\u2236Title") == "MovieTitle"  # ratio
    assert normalizer.normalize("Movie\uff1aTitle") == "MovieTitle"  # fullwidth colon
    assert (
        normalizer.normalize("Movie\u02d0Title") == "MovieTitle"
    )  # modifier letter triangular colon

    # Test multiple colons
    assert normalizer.normalize("Movie::Title") == "MovieTitle"

    # Test no change
    assert normalizer.normalize("MovieTitle") == "MovieTitle"


def test_special_dot_pattern_normalizer():
    """Test SpecialDotPatternNormalizer functionality."""
    normalizer = SpecialDotPatternNormalizer()

    # Test dash pattern
    assert normalizer.normalize("Movie.-.Title") == "Movie.Title"

    # Test plus pattern
    assert normalizer.normalize("Movie.+.Title") == "Movie.Title"

    # Test tilde pattern
    assert normalizer.normalize("Movie.~.Title") == "Movie.Title"

    # Test en-dash pattern
    assert normalizer.normalize("Movie.\u2013.Title") == "Movie.Title"

    # Test multiple patterns
    assert normalizer.normalize("Movie.-.Title.+.2021") == "Movie.Title.2021"

    # Test no change
    assert normalizer.normalize("Movie.Title.2021") == "Movie.Title.2021"


def test_end_bracket_replacement_normalizer():
    """Test EndBracketReplacementNormalizer functionality."""
    normalizer = EndBracketReplacementNormalizer()

    # Test basic bracket replacement
    assert normalizer.normalize("Movie Title[720p]") == "Movie Title-720p"
    assert normalizer.normalize("Movie Title[1080p]") == "Movie Title-1080p"
    assert normalizer.normalize("Movie Title[x264]") == "Movie Title-x264"

    # Test no replacement when already has dash at end
    assert normalizer.normalize("Movie-Title[720p]") == "Movie-Title[720p]"
    assert normalizer.normalize("Movie-Title[1080p]") == "Movie-Title[1080p]"

    # Test no brackets at end
    assert normalizer.normalize("Movie Title") == "Movie Title"
    assert normalizer.normalize("Movie[middle]Title") == "Movie[middle]Title"

    # Test empty brackets - should not change
    assert normalizer.normalize("Movie[]") == "Movie[]"


def test_parens_brackets_braces_normalizer():
    """Test ParensBracketsBracesNormalizer functionality."""
    normalizer = ParensBracketsBracesNormalizer()

    # Test parentheses
    assert normalizer.normalize("Movie(2019)") == "Movie.2019."

    # Test brackets
    assert normalizer.normalize("Movie[720p]") == "Movie.720p."

    # Test braces
    assert normalizer.normalize("Movie{x264}") == "Movie.x264."

    # Test mixed
    assert normalizer.normalize("Movie(2019)[720p]{x264}") == "Movie.2019..720p..x264."

    # Test multiple of same type
    assert normalizer.normalize("Movie((nested))") == "Movie..nested.."

    # Test no change
    assert normalizer.normalize("Movie.Title.2019") == "Movie.Title.2019"


def test_dash_dot_normalizer():
    """Test DashDotNormalizer functionality."""
    normalizer = DashDotNormalizer()

    # Test -. pattern
    assert normalizer.normalize("Movie-.Title") == "Movie.Title"

    # Test .- pattern
    assert normalizer.normalize("Movie.-Title") == "Movie.Title"

    # Test both patterns
    assert normalizer.normalize("Movie-.Title.-2021") == "Movie.Title.2021"

    # Test multiple patterns
    assert normalizer.normalize("Movie-.-.Title") == "Movie..Title"

    # Test no change
    assert normalizer.normalize("Movie.Title.2021") == "Movie.Title.2021"

    # Test isolated dashes preserved
    assert normalizer.normalize("Movie-Title") == "Movie-Title"


def test_trailing_crap_normalizer():
    """Test TrailingCrapNormalizer functionality."""
    normalizer = TrailingCrapNormalizer()

    # Test removing trailing dots
    assert normalizer.normalize("Movie.Title...") == "Movie.Title"

    # Test removing trailing dashes
    assert normalizer.normalize("Movie.Title---") == "Movie.Title"

    # Test removing trailing spaces
    assert normalizer.normalize("Movie.Title   ") == "Movie.Title"

    # Test removing mixed trailing characters
    assert normalizer.normalize("Movie.Title.-. ") == "Movie.Title"

    # Test preserving alphanumeric
    assert normalizer.normalize("Movie.Title.2021") == "Movie.Title.2021"
    assert normalizer.normalize("Movie.Title.x264") == "Movie.Title.x264"

    # Test no change
    assert normalizer.normalize("Movie.Title") == "Movie.Title"


def test_trailing_dot_normalizer():
    """Test TrailingDotNormalizer functionality."""
    normalizer = TrailingDotNormalizer()

    # Test removing single trailing dot
    assert normalizer.normalize("Movie.Title.") == "Movie.Title"

    # Test removing multiple trailing dots
    assert normalizer.normalize("Movie.Title...") == "Movie.Title"

    # Test preserving internal dots
    assert normalizer.normalize("Movie.Title.2021.") == "Movie.Title.2021"

    # Test no change when no trailing dots
    assert normalizer.normalize("Movie.Title") == "Movie.Title"
    assert normalizer.normalize("Movie.Title.2021") == "Movie.Title.2021"

    # Test empty string
    assert normalizer.normalize("") == ""

    # Test only dots
    assert normalizer.normalize("...") == ""

    # Test dots at beginning and end
    assert normalizer.normalize(".Movie.Title.") == ".Movie.Title"


def test_title_case_normalizer():
    """Test TitleCaseNormalizer functionality."""
    normalizer = TitleCaseNormalizer()

    # Test basic capitalization up to year (all lowercase)
    assert normalizer.normalize("movie.title.1999.720p.bluray") == "Movie.Title.1999.720p.bluray"

    # Test with no numeric part - should capitalize all (all lowercase)
    assert normalizer.normalize("movie.title.name") == "Movie.Title.Name"

    # Test empty string
    assert normalizer.normalize("") == ""

    # Test single word (lowercase)
    assert normalizer.normalize("movie") == "Movie"

    # Test numeric at start
    assert normalizer.normalize("2001.movie.title.bluray") == "2001.movie.title.bluray"

    # Test skipping normalization for mixed capitalization
    assert (
        normalizer.normalize("Movie.title.1999.x264") == "Movie.title.1999.x264"
    )  # mixed case (some caps), skip
    assert (
        normalizer.normalize("movie.Title.1999.x264") == "movie.Title.1999.x264"
    )  # mixed case (some caps), skip
    assert (
        normalizer.normalize("mOvIe.TiTlE.1999.x264") == "mOvIe.TiTlE.1999.x264"
    )  # mixed case (some caps), skip

    # Test normalizing ALL CAPS (should apply normalization)
    assert (
        normalizer.normalize("MOVIE.TITLE.1999.x264") == "Movie.Title.1999.x264"
    )  # all caps, should normalize
    assert (
        normalizer.normalize("LARGE.MOVIE.TITLE.1999") == "Large.Movie.Title.1999"
    )  # all caps, should normalize

    # Test ALL CAPS with short uppercase preservation
    assert (
        normalizer.normalize("BIG.MOVIE.TITLE.1999") == "BIG.Movie.Title.1999"
    )  # all caps, but BIG (3 letters) preserved as short uppercase
    assert (
        normalizer.normalize("TV.MOVIE.TITLE.1999") == "TV.Movie.Title.1999"
    )  # all caps, but TV (2 letters) preserved as short uppercase

    # Test all lowercase short words should be capitalized
    assert normalizer.normalize("big.movie.2023") == "Big.Movie.2023"
    assert normalizer.normalize("old.film.2023") == "Old.Film.2023"

    # Test edge cases - mixed capitalization should skip normalization
    assert (
        normalizer.normalize("USA.movie.title.2023") == "USA.movie.title.2023"
    )  # mixed case (USA is caps, others not), so skip
    assert (
        normalizer.normalize("ABCD.movie.title") == "ABCD.movie.title"
    )  # mixed case (ABCD is caps, others not), so skip

    # Test ALL CAPS variations that should be normalized
    assert (
        normalizer.normalize("USA.MOVIE.TITLE.2023") == "USA.Movie.Title.2023"
    )  # all caps, should normalize (USA preserved as short uppercase)
    assert (
        normalizer.normalize("ABCD.MOVIE.TITLE") == "ABCD.Movie.Title"
    )  # all caps, should normalize (ABCD preserved as 4-letter uppercase)
    assert (
        normalizer.normalize("ABCDE.MOVIE.TITLE") == "Abcde.Movie.Title"
    )  # all caps, should normalize (ABCDE is 5 letters, so gets capitalized)

    # Test all lowercase variations that should be normalized
    assert (
        normalizer.normalize("usa.movie.title.2023") == "Usa.Movie.Title.2023"
    )  # all lowercase, should normalize
    assert (
        normalizer.normalize("abcd.movie.title") == "Abcd.Movie.Title"
    )  # all lowercase, should normalize
    assert (
        normalizer.normalize("abcde.movie.title") == "Abcde.Movie.Title"
    )  # all lowercase, should normalize

    # Test cases without year
    assert normalizer.normalize("Movie.title.name") == "Movie.title.name"  # mixed case, skip
    assert (
        normalizer.normalize("MOVIE.TITLE.NAME") == "Movie.Title.NAME"
    )  # all caps, normalize (but NAME preserved as 4-letter uppercase)
    assert (
        normalizer.normalize("MOVIE.TITLE.NAMES") == "Movie.Title.Names"
    )  # all caps, normalize (NAMES is 5 letters, so gets capitalized)


def test_term_capitalizer():
    """Test TermCapitalizer functionality."""
    normalizer = TermCapitalizer()

    # Test basic BluRay capitalization (the requested example)
    assert normalizer.normalize("movie.bluray.1080p") == "movie.BluRay.1080p"
    assert normalizer.normalize("bluray") == "BluRay"
    assert normalizer.normalize("BLURAY") == "BluRay"
    assert normalizer.normalize("BluRay") == "BluRay"  # Already correct

    # Test video formats
    assert normalizer.normalize("movie.dvd.rip") == "movie.DVD.rip"
    assert normalizer.normalize("show.hdtv.720p") == "show.HDTV.720p"
    assert normalizer.normalize("film.webrip.x264") == "film.WebRip.x264"
    assert normalizer.normalize("series.webdl.1080p") == "series.WebDL.1080p"
    assert normalizer.normalize("movie.bdrip.720p") == "movie.BDRip.720p"
    assert normalizer.normalize("film.dvdrip.xvid") == "film.DVDRip.XviD"

    # Test video codecs
    assert normalizer.normalize("movie.xvid.ac3") == "movie.XviD.AC3"
    assert normalizer.normalize("film.divx.mp3") == "film.DivX.MP3"
    assert normalizer.normalize("show.x264.aac") == "show.x264.AAC"
    assert normalizer.normalize("movie.x265.hevc") == "movie.x265.HEVC"
    assert normalizer.normalize("film.h264.dts") == "film.H264.DTS"
    assert normalizer.normalize("show.h265.truehd") == "show.H265.TrueHD"

    # Test audio codecs
    assert normalizer.normalize("movie.aac.stereo") == "movie.AAC.stereo"
    assert normalizer.normalize("film.ac3.surround") == "film.AC3.surround"
    assert normalizer.normalize("show.dts.5.1") == "show.DTS.5.1"
    assert normalizer.normalize("movie.flac.lossless") == "movie.FLAC.lossless"
    assert normalizer.normalize("film.atmos.uhd") == "film.Atmos.uhd"
    assert normalizer.normalize("show.dolby.vision") == "show.Dolby.vision"

    # Test streaming services
    assert normalizer.normalize("movie.netflix.original") == "movie.Netflix.original"
    assert normalizer.normalize("show.hulu.exclusive") == "show.Hulu.exclusive"
    assert normalizer.normalize("film.amazon.prime") == "film.Amazon.prime"
    assert normalizer.normalize("series.disney.plus") == "series.Disney.plus"
    assert normalizer.normalize("movie.hbo.max") == "movie.HBO.max"
    assert normalizer.normalize("show.apple.tv") == "show.Apple.tv"

    # Test multiple terms in one string
    assert normalizer.normalize("movie.bluray.x264.ac3") == "movie.BluRay.x264.AC3"
    assert normalizer.normalize("show.hdtv.xvid.mp3") == "show.HDTV.XviD.MP3"
    assert normalizer.normalize("film.webrip.h265.aac") == "film.WebRip.H265.AAC"

    # Test case insensitive matching
    assert normalizer.normalize("MOVIE.BLURAY.X264") == "MOVIE.BluRay.x264"
    assert normalizer.normalize("Movie.BlUrAy.X264") == "Movie.BluRay.x264"

    # Test no change when term is not in the list
    assert normalizer.normalize("movie.unknown.format") == "movie.unknown.format"
    assert normalizer.normalize("completely.different.words") == "completely.different.words"

    # Test empty string
    assert normalizer.normalize("") == ""

    # Test single dot
    assert normalizer.normalize(".") == "."

    # Test terms that are substrings of other terms don't get replaced incorrectly
    assert normalizer.normalize("movie.blurayextra.x264") == "movie.blurayextra.x264"
    assert normalizer.normalize("movie.notbluray.x264") == "movie.notbluray.x264"


def test_leading_dot_normalizer():
    """Test LeadingDotNormalizer functionality."""
    normalizer = LeadingDotNormalizer()

    # Test removing single leading dot
    assert normalizer.normalize(".Movie.Title") == "Movie.Title"

    # Test removing multiple leading dots
    assert normalizer.normalize("...Movie.Title") == "Movie.Title"

    # Test preserving internal dots
    assert normalizer.normalize(".Movie.Title.2021") == "Movie.Title.2021"

    # Test no change
    assert normalizer.normalize("Movie.Title") == "Movie.Title"

    # Test only dots
    assert normalizer.normalize("...") == ""

    # Test empty string
    assert normalizer.normalize("") == ""


def test_full_normalization_pipeline():
    """Test the complete normalization pipeline with realistic examples."""

    # Complex movie filename
    result = Normalize.normalize_string("Movie Title (1999) [720p] [TGx]_..-")
    assert result == "Movie.Title.1999.720p"

    # Messy filename with multiple issues
    result = Normalize.normalize_string("...Movie_Title[rarbg]-(2021).x264...")
    assert result == "Movie.Title.2021.x264"

    # Filename with special patterns
    result = Normalize.normalize_string("Movie.-.Title.+.{2020}[ www.torrentday.com ]")
    assert result == "Movie.Title.2020"

    # Another complex example
    result = Normalize.normalize_string("Movie__Title[EtHD]  (2018)-.x265")
    assert result == "Movie.Title.2018.x265"

    # Test that multiple dots from brackets get collapsed
    result = Normalize.normalize_string("Movie(2019)[720p]{x264}")
    assert result == "Movie.2019.720p.x264"

    # Test TermCapitalizer integration in pipeline
    result = Normalize.normalize_string("Movie Title (2019) [bluray] x264")
    assert result == "Movie.Title.2019.BluRay.x264"

    # Test multiple term capitalizations in pipeline
    result = Normalize.normalize_string("Movie__hdtv__xvid__ac3")
    assert result == "Movie.HDTV.XviD.AC3"


def test_normalization_pipeline_edge_cases():
    """Test edge cases in the normalization pipeline."""

    # Empty string
    assert Normalize.normalize_string("") == ""

    # Only special characters
    assert Normalize.normalize_string("...---___") == ""

    # No changes needed
    assert Normalize.normalize_string("Clean.Movie.Title") == "Clean.Movie.Title"

    # Multiple iterations needed
    result = Normalize.normalize_string("((Movie))  Title__[[2021]]")
    assert result == "Movie.Title.2021"


def test_case_insensitive_filesystem_detection():
    """Test case-insensitive filesystem detection and safety checks."""
    import os
    import tempfile

    from tidyflix.operations.normalize import (
        check_case_only_rename_safety,
        is_case_insensitive_filesystem,
    )

    # Test with a temporary directory (usually case-sensitive on Linux)
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test case-insensitive detection
        is_case_insensitive = is_case_insensitive_filesystem(temp_dir)

        # On most Linux filesystems, this should be False
        # but we can't assume - just test that the function works
        assert isinstance(is_case_insensitive, bool)

        # Test safety check for case-only changes
        old_path = os.path.join(temp_dir, "movie.title.2023")
        new_path = os.path.join(temp_dir, "Movie.Title.2023")

        is_safe = check_case_only_rename_safety(old_path, new_path, temp_dir)
        assert isinstance(is_safe, bool)

        # Test non-case-only change (should always be safe)
        different_path = os.path.join(temp_dir, "completely.different.name")
        is_safe_diff = check_case_only_rename_safety(old_path, different_path, temp_dir)
        assert is_safe_diff is True


def test_normalize_with_case_insensitive_filesystem_simulation():
    """Test normalize behavior when case-insensitive filesystem is detected."""
    import os
    import tempfile
    from unittest.mock import patch

    from tidyflix.operations.normalize import normalize_directories

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a directory with lowercase name
        test_dir = os.path.join(temp_dir, "movie.title.2023")
        os.makedirs(test_dir)

        # The expected uppercase path that would exist on case-insensitive filesystem
        uppercase_path = os.path.join(temp_dir, "Movie.Title.2023")

        # Mock os.path.exists to simulate case-insensitive filesystem
        # where the uppercase path "exists" (refers to same dir as lowercase)
        original_exists = os.path.exists

        def mock_exists(path: str) -> bool:
            if path == uppercase_path:
                return True  # Simulate case-insensitive filesystem behavior
            return original_exists(path)

        # Mock both os.path.exists and case-insensitive filesystem detection
        with (
            patch("os.path.exists", side_effect=mock_exists),
            patch(
                "tidyflix.operations.normalize.is_case_insensitive_filesystem", return_value=True
            ),
        ):
            # This should now detect the unsafe condition and skip the rename
            result = normalize_directories(
                target_directories=[temp_dir], dry_run=False, explain=False
            )

            # The operation should report failure due to unsafe filesystem
            assert result is False

            # Original directory should still exist
            assert os.path.exists(test_dir)
