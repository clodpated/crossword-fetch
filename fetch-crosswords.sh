#!/bin/bash
#
# fetch-crosswords.sh — Download the latest .puz files from all non-cryptic sources
#
# Puzzles are saved to ~/Crosswords/YYYY-MM/ organized by month.
# A log is written to ~/Crosswords/logs/
#
# Designed to run hourly via cron/launchd. Uses a stamp file to ensure
# downloads are only attempted once per day.

set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"

DATE=$(date +%Y-%m-%d)
MONTH=$(date +%Y-%m)
OUTDIR="$HOME/Crosswords/$MONTH"
LOGDIR="$HOME/Crosswords/logs"
LOGFILE="$LOGDIR/$DATE.log"
STAMP="$LOGDIR/.fetched-$DATE"

mkdir -p "$OUTDIR" "$LOGDIR"

# Skip if already fetched today
if [ -f "$STAMP" ]; then
    exit 0
fi

log() {
    echo "[$(date '+%H:%M:%S')] $*" >> "$LOGFILE"
}

download() {
    local code="$1"
    local label="$2"
    local extra="${3:-}"

    log "Fetching $label ($code)..."
    if eval xword-dl "$code" $extra -o "$OUTDIR/%Y-%m-%d - %prefix - %title - %author" >> "$LOGFILE" 2>&1; then
        log "  OK: $label"
    else
        log "  FAILED: $label — retrying in 5s..."
        sleep 5
        if eval xword-dl "$code" $extra -o "$OUTDIR/%Y-%m-%d - %prefix - %title - %author" >> "$LOGFILE" 2>&1; then
            log "  OK: $label (retry)"
        else
            log "  FAILED: $label (gave up)"
        fi
    fi
    sleep 2
}

log "=== xword-dl fetch started ==="

# --- NYT (requires authentication) ---
download nyt   "New York Times"
download nytm  "New York Times Mini"
download nytd  "New York Times Midi"
download nytv  "New York Times Variety" "-d today"

# --- Major US Dailies (free) ---
download lat   "Los Angeles Times"
download latm  "Los Angeles Times Mini"
download usa   "USA Today"
# uni handled by fetch-extras.py (xword-dl blocked by user-agent filter)
download nd    "Newsday"
download wp    "Washington Post"
download pop   "Daily Pop"

# --- Puzzmo ---
download pzm   "Puzzmo"
download pzmb  "Puzzmo Big"

# --- Weekly / Periodic ---
download tny   "The New Yorker"
download tnym  "The New Yorker Mini"
download atl   "The Atlantic"
download bill  "Billboard"
download vox   "Vox"
download vult  "Vulture"
download db    "The Daily Beast"
download wal   "The Walrus"
download club  "Crossword Club"

# --- Extras (Universal daily/Sunday + WSJ via fetch-extras.py) ---
log "Running fetch-extras.py..."
uv run --with requests --with puzpy "$HOME/Crosswords/fetch-extras.py" --date "$DATE" --outdir "$OUTDIR" >> "$LOGFILE" 2>&1

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
PUZZLES=$(find "$OUTDIR" -name "${DATE}*\.puz" 2>/dev/null | wc -l | tr -d ' ')
log "Downloaded $PUZZLES puzzle(s) for $DATE"

# Mark today as fetched so hourly runs skip
touch "$STAMP"

echo "Downloaded $PUZZLES puzzle(s) for $DATE"
