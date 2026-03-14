#!/bin/bash
#
# backfill.sh — Download historical puzzles for a date range
#
# Downloads from all sources that support date-based fetching (xword-dl -d)
# plus Universal/WSJ/Universal Sunday via fetch-extras.py.
# Skips any date+source that already has a .puz file.
#
# Usage:
#   ./backfill.sh --start 2026-01-01 --end 2026-03-01
#
# Note: Sources that only support --latest (Billboard, Daily Beast, Vox,
# The Walrus) are excluded — they can't fetch by date.

set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOGDIR="$HOME/Crosswords/logs"
LOGFILE="$LOGDIR/backfill.log"
mkdir -p "$LOGDIR"

log() {
    echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOGFILE"
}

# shellcheck source=_shared.sh
source "$SCRIPT_DIR/_shared.sh"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
START=""
END=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --start) START="$2"; shift 2 ;;
        --end)   END="$2";   shift 2 ;;
        *)       echo "Usage: $0 --start YYYY-MM-DD --end YYYY-MM-DD"; exit 1 ;;
    esac
done

if [[ -z "$START" || -z "$END" ]]; then
    echo "Usage: $0 --start YYYY-MM-DD --end YYYY-MM-DD"
    exit 1
fi

# ---------------------------------------------------------------------------
# Cross-platform date increment (macOS vs GNU/Linux)
# ---------------------------------------------------------------------------
next_day() {
    # macOS (BSD date)
    if date -j -v+1d -f "%Y-%m-%d" "$1" +%Y-%m-%d 2>/dev/null; then
        return
    fi
    # Linux (GNU date)
    date -d "$1 + 1 day" +%Y-%m-%d
}

# ---------------------------------------------------------------------------
# Sources that support xword-dl -d DATE
# Format: code:prefix (prefix must match fetch-crosswords.sh naming)
# ---------------------------------------------------------------------------
SOURCES=(
    "nyt:NY Times"
    "nytm:NY Times Mini"
    "nytd:NY Times Midi"
    "nytv:NY Times Variety"
    "lat:LA Times"
    "latm:LA Times Mini"
    "usa:USA Today"
    "nd:Newsday"
    "wp:WaPo"
    "pop:Daily Pop"
    "pzm:Puzzmo"
    "pzmb:Puzzmo Big"
    "tny:New Yorker"
    "tnym:New Yorker Mini"
    "atl:Atlantic"
    "vult:Vulture"
    "club:Crossword Club"
)

# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
log "=== Backfill $START → $END ==="

current="$START"
while [[ "$current" < "$END" || "$current" == "$END" ]]; do
    MONTH="${current%-[0-9][0-9]}"  # 2026-01-15 → 2026-01
    OUTDIR="$HOME/Crosswords/$MONTH"
    mkdir -p "$OUTDIR"

    log "--- $current ---"

    # xword-dl sources
    for entry in "${SOURCES[@]}"; do
        code="${entry%%:*}"
        prefix="${entry#*:}"

        if has_puzzle "$OUTDIR" "$current" "$prefix"; then
            continue
        fi

        if xword-dl "$code" -d "$current" -o "$OUTDIR/%Y-%m-%d - %prefix - %title - %author" >> "$LOGFILE" 2>&1; then
            log "  OK: $code"
        else
            log "  SKIP: $code"
        fi
        sleep 1
    done

    # Clean up empty title/author placeholders
    clean_filenames "$OUTDIR" "$current"

    # Universal, WSJ, Universal Sunday via fetch-extras.py
    if uv run --with requests --with puzpy "$SCRIPT_DIR/fetch-extras.py" --date "$current" --outdir "$OUTDIR" >> "$LOGFILE" 2>&1; then
        true  # logged by fetch-extras.py
    else
        log "  FAILED: fetch-extras.py"
    fi

    current=$(next_day "$current")
done

TOTAL=$(find "$HOME/Crosswords" -name '*.puz' 2>/dev/null | wc -l | tr -d ' ')
log "=== Backfill complete. $TOTAL total .puz files in library ==="
