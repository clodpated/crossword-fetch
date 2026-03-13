#!/usr/bin/env python3
"""
rename-library.py — Rename all .puz files to the human-readable convention:

    YYYY-MM-DD - Publisher - Title - Author.puz

Reads title/author from each .puz file's metadata.
Uses "Untitled" for missing title, "Unlisted" for missing author.

Determines the publisher prefix from either:
  - The old code-based filename (e.g. nyt-20260113.puz → "NY Times")
  - The folder date + .puz metadata for files already in new format

Usage:
    python3 rename-library.py [--dry-run]
"""

import argparse
import re
import sys
from pathlib import Path

import puz

# Map xword-dl command codes → outlet_prefix (from xword-dl source)
CODE_TO_PREFIX = {
    "nyt":   "NY Times",
    "nytm":  "NY Times Mini",
    "nytd":  "NY Times Midi",
    "nytv":  "NY Times Variety",
    "lat":   "LA Times",
    "latm":  "LA Times Mini",
    "usa":   "USA Today",
    "uni":   "Universal",
    "nd":    "Newsday",
    "wp":    "WaPo",
    "pop":   "Daily Pop",
    "pzm":   "Puzzmo",
    "pzmb":  "Puzzmo Big",
    "tny":   "New Yorker",
    "tnym":  "New Yorker Mini",
    "atl":   "Atlantic",
    "bill":  "Billboard",
    "vox":   "Vox",
    "vult":  "Vulture",
    "db":    "Daily Beast",
    "wal":   "The Walrus",
    "club":  "Crossword Club",
    # fetch-extras.py sources
    "wsj":   "WSJ",
    "ucsun": "Universal Sunday",
}

# For files already in new format, map known prefix strings back
# (in case they need title/author fixup)
KNOWN_PREFIXES = set(CODE_TO_PREFIX.values())


def safe_filename(s):
    """Remove characters illegal in filenames."""
    return re.sub(r'[/:*?"<>|]', '', s).strip()


def extract_code(filename):
    """Extract the source code from old-format filenames like 'nyt-20260113.puz'."""
    # Match: code-YYYYMMDD.puz  (code may contain letters/digits)
    m = re.match(r'^([a-z]+)-\d{8}\.puz$', filename)
    if m:
        return m.group(1)
    return None


def extract_prefix_from_new_format(filename):
    """Try to extract the publisher prefix from a new-format filename."""
    # Pattern: YYYY-MM-DD - Publisher - Title - Author.puz
    # Also handles older format without " - " after date (space only)
    m = re.match(r'^\d{4}-\d{2}-\d{2}\s+(?:-\s+)?(.+?)\s+-\s+', filename)
    if m:
        prefix = m.group(1)
        if prefix in KNOWN_PREFIXES:
            return prefix
    return None


def build_new_name(date_str, prefix, title, author):
    """Build the new filename."""
    parts = [
        date_str,
        prefix,
        title if title else "Untitled",
        author if author else "Unlisted",
    ]
    return safe_filename(" - ".join(parts)) + ".puz"


def get_date_from_parent(filepath):
    """Get the YYYY-MM-DD date from the parent folder name."""
    parent = filepath.parent.name
    if re.match(r'^\d{4}-\d{2}-\d{2}$', parent):
        return parent
    return None


def main():
    parser = argparse.ArgumentParser(description="Rename .puz library to new convention")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be renamed without doing it")
    args = parser.parse_args()

    base = Path.home() / "Crosswords"
    puz_files = sorted(base.rglob("*.puz"))

    renamed = 0
    skipped = 0
    dupes = 0
    errors = 0
    seen_targets = set()  # track targets to detect duplicates in dry-run

    for f in puz_files:
        # Skip temp files
        if f.name.startswith("."):
            continue

        date_str = get_date_from_parent(f)
        if not date_str:
            print(f"  SKIP (no date folder): {f}")
            skipped += 1
            continue

        # Determine publisher prefix
        code = extract_code(f.name)
        if code and code in CODE_TO_PREFIX:
            prefix = CODE_TO_PREFIX[code]
        else:
            # Maybe already in new format
            prefix = extract_prefix_from_new_format(f.name)
            if not prefix:
                print(f"  SKIP (unknown format): {f.name}")
                skipped += 1
                continue

        # Read .puz metadata
        try:
            p = puz.read(str(f))
            title = (p.title or "").strip()
            author = (p.author or "").strip()
        except Exception as e:
            print(f"  WARN reading {f.name}: {e} (using Untitled/Unlisted)")
            title = ""
            author = ""

        new_name = build_new_name(date_str, prefix, title, author)
        new_path = f.parent / new_name

        # Already correct?
        if f.name == new_name:
            seen_targets.add(new_path)
            skipped += 1
            continue

        # Collision check (on-disk or already claimed by an earlier rename)
        if (new_path.exists() and new_path != f) or new_path in seen_targets:
            print(f"  DUPE: {f.name} → {new_name} (duplicate, removing)")
            if not args.dry_run:
                f.unlink()
            dupes += 1
            continue

        seen_targets.add(new_path)

        if args.dry_run:
            print(f"  {f.name}")
            print(f"    → {new_name}")
        else:
            f.rename(new_path)

        renamed += 1

    action = "Would rename" if args.dry_run else "Renamed"
    print(f"\n{action} {renamed} file(s), skipped {skipped}, dupes removed {dupes}, errors {errors}")


if __name__ == "__main__":
    main()
