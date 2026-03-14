#!/usr/bin/env python3
"""
fetch-extras.py — Download puzzles that xword-dl can't reliably handle.

Sources:
  - Universal Daily  (AMUniversal API — xword-dl blocked by user-agent)
  - WSJ Daily        (herbach.dnsalias.com — not in xword-dl)
  - Universal Sunday (herbach.dnsalias.com — not in xword-dl)

Usage:
  python3 fetch-extras.py [--date YYYY-MM-DD]
"""

import argparse
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import puz
import requests

# Browser user-agent — some APIs reject Python's default UA.
# Update the Chrome version periodically to avoid stale-UA rejections.
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}")


def safe_filename(s):
    """Remove characters that are illegal in filenames."""
    return re.sub(r'[/:*?"<>|]', '', s).strip()


def puz_filename(dt, prefix, title, author):
    """Build a human-readable filename matching the xword-dl convention."""
    parts = [
        f"{dt:%Y-%m-%d}",
        prefix,
        title if title else "Untitled",
        author if author else "Unlisted",
    ]
    return safe_filename(" - ".join(parts)) + ".puz"


def file_exists_for(outdir, dt, prefix):
    """Check if a .puz file for this date+prefix already exists in outdir."""
    date_str = f"{dt:%Y-%m-%d}"
    return any(outdir.glob(f"{date_str} - {prefix} - *.puz"))


# ---------------------------------------------------------------------------
# Universal Daily via AMUniversal JSON API
# ---------------------------------------------------------------------------
UNI_BLOB = (
    "https://gamedata.services.amuniversal.com/c/uucom/l/"
    "U2FsdGVkX18YuMv20%2B8cekf85%2Friz1H%2FzlWW4bn0cizt8yclLsp7UYv34S77X0aX"
    "%0Axa513fPTc5RoN2wa0h4ED9QWuBURjkqWgHEZey0WFL8%3D/g/fcx/d/"
)


def fetch_universal_api(dt, outdir):
    """Download the Universal crossword for a given date via the JSON API."""
    if file_exists_for(outdir, dt, "Universal"):
        log("  SKIP Universal (already exists)")
        return True

    url = f"{UNI_BLOB}{dt:%Y-%m-%d}/data.json"

    try:
        r = SESSION.get(url, timeout=15)
        r.raise_for_status()
        xw = r.json()
    except (requests.RequestException, ValueError) as e:
        log(f"  FAILED Universal API: {e}")
        return False

    try:
        puzzle = puz.Puzzle()
        puzzle.title = unquote(xw.get("Title", "")).strip()
        puzzle.author = " / Ed. ".join(
            filter(None, [
                unquote(xw.get("Author", "")).strip(),
                unquote(xw.get("Editor", "")).strip(),
            ])
        )
        puzzle.copyright = unquote(xw.get("Copyright", "")).strip()
        puzzle.width = int(xw["Width"])
        puzzle.height = int(xw["Height"])
        puzzle.solution = xw["AllAnswer"].replace("-", ".")
        puzzle.fill = "".join("." if c == "." else "-" for c in puzzle.solution)

        across = xw["AcrossClue"].splitlines()
        down = xw["DownClue"].splitlines()
        clues = sorted(
            [{"num": c.split("|", 1)[0], "clue": c.split("|", 1)[1]} for c in across + down],
            key=lambda x: int(x["num"]),
        )
        puzzle.clues = [c["clue"] for c in clues]

        fname = puz_filename(dt, "Universal", puzzle.title, puzzle.author)
        outpath = outdir / fname
        puzzle.save(str(outpath))
        log(f"  OK Universal → {outpath.name}")
        return True
    except (KeyError, ValueError, TypeError) as e:
        log(f"  FAILED Universal (parse): {e}")
        return False


# ---------------------------------------------------------------------------
# herbach.dnsalias.com direct .puz downloads
# No authentication required — just needs a browser user-agent.
#
# URL patterns (from Cruciverb / Crossword Fiend):
#   WSJ daily:        /wsj/wsj{YYMMDD}.puz
#   Universal daily:  /uc/uc{YYMMDD}.puz      (fallback if API fails)
#   Universal Sunday: /uc/ucs{YYMMDD}.puz
# ---------------------------------------------------------------------------
HERBACH_BASE = "https://herbach.dnsalias.com"

HERBACH_SOURCES = {
    "wsj":    ("WSJ",              "/wsj/wsj{ymd}.puz"),
    "uc":     ("Universal",        "/uc/uc{ymd}.puz"),
    "ucsun":  ("Universal Sunday", "/uc/ucs{ymd}.puz"),
}


def fetch_herbach(key, dt, outdir):
    """Download a .puz file from herbach.dnsalias.com and rename with metadata."""
    label, path_tmpl = HERBACH_SOURCES[key]

    if file_exists_for(outdir, dt, label):
        log(f"  SKIP {label} (already exists)")
        return True

    ymd = dt.strftime("%y%m%d")
    url = HERBACH_BASE + path_tmpl.format(ymd=ymd)

    try:
        r = SESSION.get(url, timeout=15)
        if r.status_code == 200 and len(r.content) > 100:
            # Save to temp, read metadata, rename
            tmp = outdir / f".tmp-{key}.puz"
            tmp.write_bytes(r.content)
            try:
                try:
                    p = puz.read(str(tmp))
                    fname = puz_filename(dt, label, p.title, p.author)
                except Exception:
                    fname = puz_filename(dt, label, "", "")
                final = outdir / fname
                tmp.rename(final)
            except Exception:
                # Clean up temp file if rename or anything else fails
                tmp.unlink(missing_ok=True)
                raise
            log(f"  OK {label} → {final.name}")
            return True
        elif r.status_code == 404:
            log(f"  SKIP {label} (not published for {dt:%Y-%m-%d})")
            return False
        else:
            log(f"  FAILED {label} (HTTP {r.status_code})")
            return False
    except Exception as e:
        log(f"  FAILED {label}: {e}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Fetch extra crossword puzzles")
    parser.add_argument("--date", help="Date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--outdir", help="Override output directory")
    args = parser.parse_args()

    dt = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.today()
    outdir = Path(args.outdir) if args.outdir else Path.home() / "Crosswords" / f"{dt:%Y-%m}"
    outdir.mkdir(parents=True, exist_ok=True)

    log(f"=== fetch-extras for {dt:%Y-%m-%d} ===")

    # Universal daily: try API first, fall back to herbach .puz
    if not fetch_universal_api(dt, outdir):
        fetch_herbach("uc", dt, outdir)

    # WSJ daily (Mon-Sat, no Sunday puzzle)
    fetch_herbach("wsj", dt, outdir)

    # Universal Sunday (only on Sundays, but try anyway — server returns 404 for other days)
    if dt.weekday() == 6:  # Sunday
        fetch_herbach("ucsun", dt, outdir)

    log("=== fetch-extras complete ===")


if __name__ == "__main__":
    main()
