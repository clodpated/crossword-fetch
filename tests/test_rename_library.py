"""Tests for the pure functions in rename-library.py."""

import pytest

from rename_library import (
    safe_filename,
    extract_code_and_date,
    extract_prefix_from_new_format,
    build_new_name,
    extract_date_from_filename,
    CODE_TO_PREFIX,
)


# ---------------------------------------------------------------------------
# safe_filename
# ---------------------------------------------------------------------------
class TestSafeFilename:
    def test_passthrough_clean_string(self):
        assert safe_filename("Hello World") == "Hello World"

    def test_strips_colons(self):
        assert safe_filename("Title: Subtitle") == "Title Subtitle"

    def test_strips_slashes(self):
        assert safe_filename("A/B") == "AB"

    def test_strips_question_marks(self):
        assert safe_filename("Really?") == "Really"

    def test_strips_quotes(self):
        assert safe_filename('"Quoted"') == "Quoted"

    def test_strips_angle_brackets(self):
        assert safe_filename("<tag>") == "tag"

    def test_strips_pipes(self):
        assert safe_filename("A|B") == "AB"

    def test_strips_asterisks(self):
        assert safe_filename("star*power") == "starpower"

    def test_strips_leading_trailing_whitespace(self):
        assert safe_filename("  padded  ") == "padded"

    def test_multiple_illegal_chars(self):
        assert safe_filename('A:B/C*D?"E') == "ABCDE"


# ---------------------------------------------------------------------------
# extract_code_and_date
# ---------------------------------------------------------------------------
class TestExtractCodeAndDate:
    def test_nyt(self):
        assert extract_code_and_date("nyt-20260113.puz") == ("nyt", "2026-01-13")

    def test_multi_char_code(self):
        assert extract_code_and_date("nytm-20260215.puz") == ("nytm", "2026-02-15")

    def test_long_code(self):
        assert extract_code_and_date("ucsun-20260301.puz") == ("ucsun", "2026-03-01")

    def test_non_matching_random(self):
        assert extract_code_and_date("random.puz") == (None, None)

    def test_new_format_returns_none(self):
        assert extract_code_and_date(
            "2026-01-13 - NY Times - Title - Author.puz"
        ) == (None, None)

    def test_no_extension(self):
        assert extract_code_and_date("nyt-20260113") == (None, None)

    def test_uppercase_code_no_match(self):
        assert extract_code_and_date("NYT-20260113.puz") == (None, None)

    def test_extra_digits(self):
        assert extract_code_and_date("nyt-202601130.puz") == (None, None)


# ---------------------------------------------------------------------------
# extract_prefix_from_new_format
# ---------------------------------------------------------------------------
class TestExtractPrefixFromNewFormat:
    def test_ny_times(self):
        assert (
            extract_prefix_from_new_format(
                "2026-01-13 - NY Times - Thursday - Author.puz"
            )
            == "NY Times"
        )

    def test_wapo(self):
        assert (
            extract_prefix_from_new_format(
                "2026-03-13 - WaPo - Some Title - Author.puz"
            )
            == "WaPo"
        )

    def test_puzzmo(self):
        assert (
            extract_prefix_from_new_format(
                "2026-01-01 - Puzzmo - Blast Off! - Willa.puz"
            )
            == "Puzzmo"
        )

    def test_unknown_prefix_returns_none(self):
        assert (
            extract_prefix_from_new_format(
                "2026-01-13 - Unknown Source - Title - Author.puz"
            )
            is None
        )

    def test_old_format_returns_none(self):
        assert extract_prefix_from_new_format("nyt-20260113.puz") is None

    def test_all_known_prefixes_round_trip(self):
        """Every known prefix should be extractable from a constructed filename."""
        for prefix in CODE_TO_PREFIX.values():
            fname = f"2026-01-01 - {prefix} - Test - Author.puz"
            assert extract_prefix_from_new_format(fname) == prefix, (
                f"Failed to extract prefix '{prefix}' from '{fname}'"
            )


# ---------------------------------------------------------------------------
# build_new_name
# ---------------------------------------------------------------------------
class TestBuildNewName:
    def test_all_fields(self):
        result = build_new_name("2026-01-13", "NY Times", "Thursday", "John Doe")
        assert result == "2026-01-13 - NY Times - Thursday - John Doe.puz"

    def test_empty_title(self):
        result = build_new_name("2026-01-13", "NY Times", "", "John Doe")
        assert result == "2026-01-13 - NY Times - Untitled - John Doe.puz"

    def test_empty_author(self):
        result = build_new_name("2026-01-13", "NY Times", "Thursday", "")
        assert result == "2026-01-13 - NY Times - Thursday - Unlisted.puz"

    def test_both_empty(self):
        result = build_new_name("2026-01-13", "USA Today", "", "")
        assert result == "2026-01-13 - USA Today - Untitled - Unlisted.puz"

    def test_illegal_chars_in_title(self):
        result = build_new_name("2026-01-13", "NY Times", "Title: Part 1/2", "Author")
        assert ":" not in result
        assert "/" not in result
        assert result.endswith(".puz")

    def test_none_title_treated_as_empty(self):
        result = build_new_name("2026-01-13", "Puzzmo", None, "Willa")
        assert "Untitled" in result

    def test_none_author_treated_as_empty(self):
        result = build_new_name("2026-01-13", "Puzzmo", "Blast Off!", None)
        assert "Unlisted" in result


# ---------------------------------------------------------------------------
# extract_date_from_filename
# ---------------------------------------------------------------------------
class TestExtractDateFromFilename:
    def test_new_format(self):
        assert (
            extract_date_from_filename(
                "2026-03-13 - NY Times - Title - Author.puz"
            )
            == "2026-03-13"
        )

    def test_old_format(self):
        assert extract_date_from_filename("nyt-20260313.puz") == "2026-03-13"

    def test_old_format_multi_char_code(self):
        assert extract_date_from_filename("latm-20260101.puz") == "2026-01-01"

    def test_unrecognized(self):
        assert extract_date_from_filename("random-file.puz") is None

    def test_no_extension(self):
        assert extract_date_from_filename("nyt-20260313") is None

    def test_new_format_date_only(self):
        # Just date with a space after it (minimal new-format match)
        assert extract_date_from_filename("2026-12-25 something.puz") == "2026-12-25"
