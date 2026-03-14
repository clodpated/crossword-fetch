#!/bin/bash
#
# fetch-crosswords.sh — Download the latest .puz files from all non-cryptic sources
#
# Puzzles are saved to ~/Crosswords/YYYY-MM/ organized by month.
# A log is written to ~/Crosswords/logs/
#
# Designed to run hourly via cron/launchd. Each source is skipped if its
# puzzle for today already exists, so repeated runs only fetch what's missing.

set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATE=$(date +%Y-%m-%d)
MONTH=$(date +%Y-%m)
OUTDIR="$HOME/Crosswords/$MONTH"
LOGDIR="$HOME/Crosswords/logs"
LOGFILE="$LOGDIR/$DATE.log"

mkdir -p "$OUTDIR" "$LOGDIR"

log() {
    echo "[$(date '+%H:%M:%S')] $*" >> "$LOGFILE"
}

has_puzzle() {
    # Check if a .puz file for this date+prefix already exists
    ls "$OUTDIR"/${DATE}*.puz 2>/dev/null | grep -q " - ${1} - "
}

download() {
    local code="$1"
    local prefix="$2"
    shift 2
    local -a extra=("$@")

    # Skip if we already have this puzzle
    if has_puzzle "$prefix"; then
        return
    fi

    local -a cmd=(xword-dl "$code" "${extra[@]}" -o "$OUTDIR/%Y-%m-%d - %prefix - %title - %author")

    log "Fetching $prefix ($code)..."
    if "${cmd[@]}" >> "$LOGFILE" 2>&1; then
        log "  OK: $prefix"
    else
        log "  FAILED: $prefix — retrying in 5s..."
        sleep 5
        if "${cmd[@]}" >> "$LOGFILE" 2>&1; then
            log "  OK: $prefix (retry)"
        else
            log "  FAILED: $prefix (gave up)"
        fi
    fi
    sleep 2
}

log "=== xword-dl fetch started ==="

# --- NYT (requires authentication) ---
download nyt   "NY Times"
download nytm  "NY Times Mini"
download nytd  "NY Times Midi"
download nytv  "NY Times Variety" -d today

# --- Major US Dailies (free) ---
download lat   "LA Times"
download latm  "LA Times Mini"
download usa   "USA Today"
# uni handled by fetch-extras.py (xword-dl blocked by user-agent filter)
download nd    "Newsday"
download wp    "WaPo"
download pop   "Daily Pop"

# --- Puzzmo ---
download pzm   "Puzzmo"
download pzmb  "Puzzmo Big"

# --- Weekly / Periodic ---
download tny   "New Yorker"
download tnym  "New Yorker Mini"
download atl   "Atlantic"
download bill  "Billboard"
download vox   "Vox"
download vult  "Vulture"
download db    "Daily Beast"
download wal   "The Walrus"
download club  "Crossword Club"

# --- Extras (Universal daily/Sunday + WSJ via fetch-extras.py) ---
log "Running fetch-extras.py..."
if uv run --with requests --with puzpy "$SCRIPT_DIR/fetch-extras.py" --date "$DATE" --outdir "$OUTDIR" >> "$LOGFILE" 2>&1; then
    log "  OK: fetch-extras.py"
else
    log "  FAILED: fetch-extras.py"
fi

log "=== xword-dl fetch complete ==="

# Clean up filenames: fill in placeholders for empty title/author tokens
for f in "$OUTDIR"/${DATE}*.puz; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    # Pattern: "date - prefix - TITLE - AUTHOR.puz"
    # Detect empty title (double dash) or trailing empty author
    clean=$(echo "$name" | sed \
        's/\( - [^-]*\) - - \(.*\)\.puz/\1 - Untitled - \2.puz/' \
    )
    # If author is empty (trailing " - .puz")
    clean=$(echo "$clean" | sed 's/ - \.puz/ - Unlisted.puz/')
    # If both were empty, title is now "Untitled" but author might still be empty
    clean=$(echo "$clean" | sed 's/ - Untitled - \.puz/ - Untitled - Unlisted.puz/')
    if [ "$name" != "$clean" ]; then
        mv "$f" "$OUTDIR/$clean"
        log "  Renamed → $clean"
    fi
done

# Count today's results
PUZZLES=$(find "$OUTDIR" -name "${DATE} -*\.puz" 2>/dev/null | wc -l | tr -d ' ')
log "Downloaded $PUZZLES puzzle(s) for $DATE"

echo "Downloaded $PUZZLES puzzle(s) for $DATE"
