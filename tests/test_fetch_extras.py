"""Tests for the pure functions in fetch-extras.py."""

import importlib.util
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Load fetch-extras.py as a module despite the hyphenated filename
_spec = importlib.util.spec_from_file_location(
    "fetch_extras",
    Path(__file__).resolve().parent.parent / "fetch-extras.py",
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["fetch_extras"] = _mod
_spec.loader.exec_module(_mod)

safe_filename = _mod.safe_filename
puz_filename = _mod.puz_filename
file_exists_for = _mod.file_exists_for


# ---------------------------------------------------------------------------
# safe_filename
# ---------------------------------------------------------------------------
class TestSafeFilename:
    def test_passthrough_clean_string(self):
        assert safe_filename("Hello World") == "Hello World"

    def test_strips_colons(self):
        assert safe_filename("Title: Subtitle") == "Title Subtitle"

    def test_strips_multiple_illegal_chars(self):
        assert safe_filename('A:B/C*D?"E') == "ABCDE"

    def test_strips_leading_trailing_whitespace(self):
        assert safe_filename("  padded  ") == "padded"


# ---------------------------------------------------------------------------
# puz_filename
# ---------------------------------------------------------------------------
class TestPuzFilename:
    def test_normal_case(self):
        dt = datetime(2026, 1, 13)
        result = puz_filename(dt, "NY Times", "Thursday", "John Doe")
        assert result == "2026-01-13 - NY Times - Thursday - John Doe.puz"

    def test_empty_title(self):
        dt = datetime(2026, 3, 1)
        result = puz_filename(dt, "Puzzmo", "", "Willa")
        assert result == "2026-03-01 - Puzzmo - Untitled - Willa.puz"

    def test_empty_author(self):
        dt = datetime(2026, 3, 1)
        result = puz_filename(dt, "Puzzmo", "Blast Off!", "")
        assert result == "2026-03-01 - Puzzmo - Blast Off! - Unlisted.puz"

    def test_both_empty(self):
        dt = datetime(2026, 1, 1)
        result = puz_filename(dt, "USA Today", "", "")
        assert result == "2026-01-01 - USA Today - Untitled - Unlisted.puz"

    def test_illegal_chars_in_title(self):
        dt = datetime(2026, 2, 14)
        result = puz_filename(dt, "Universal", "Love: A/B", "Author")
        assert ":" not in result
        assert "/" not in result
        assert result.endswith(".puz")

    def test_date_formatting(self):
        dt = datetime(2025, 7, 4)
        result = puz_filename(dt, "WSJ", "Title", "Author")
        assert result.startswith("2025-07-04")


# ---------------------------------------------------------------------------
# file_exists_for
# ---------------------------------------------------------------------------
class TestFileExistsFor:
    def test_matching_file(self, tmp_path):
        # Create a file that matches the date and prefix
        (tmp_path / "2026-01-13 - NY Times - Title - Author.puz").touch()
        dt = datetime(2026, 1, 13)
        assert file_exists_for(tmp_path, dt, "NY Times") is True

    def test_wrong_date(self, tmp_path):
        (tmp_path / "2026-01-13 - NY Times - Title - Author.puz").touch()
        dt = datetime(2026, 1, 14)
        assert file_exists_for(tmp_path, dt, "NY Times") is False

    def test_wrong_prefix(self, tmp_path):
        (tmp_path / "2026-01-13 - NY Times - Title - Author.puz").touch()
        dt = datetime(2026, 1, 13)
        assert file_exists_for(tmp_path, dt, "WaPo") is False

    def test_empty_directory(self, tmp_path):
        dt = datetime(2026, 1, 13)
        assert file_exists_for(tmp_path, dt, "NY Times") is False

    def test_non_puz_file_ignored(self, tmp_path):
        (tmp_path / "2026-01-13 - NY Times - Title - Author.txt").touch()
        dt = datetime(2026, 1, 13)
        assert file_exists_for(tmp_path, dt, "NY Times") is False

    def test_multiple_files_different_prefixes(self, tmp_path):
        (tmp_path / "2026-01-13 - NY Times - Title - Author.puz").touch()
        (tmp_path / "2026-01-13 - WaPo - Title - Author.puz").touch()
        dt = datetime(2026, 1, 13)
        assert file_exists_for(tmp_path, dt, "NY Times") is True
        assert file_exists_for(tmp_path, dt, "WaPo") is True
        assert file_exists_for(tmp_path, dt, "Puzzmo") is False

    def test_untitled_unlisted_file(self, tmp_path):
        (tmp_path / "2026-01-13 - USA Today - Untitled - Unlisted.puz").touch()
        dt = datetime(2026, 1, 13)
        assert file_exists_for(tmp_path, dt, "USA Today") is True
