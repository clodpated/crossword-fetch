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

# shellcheck source=_shared.sh
source "$SCRIPT_DIR/_shared.sh"

download() {
    local code="$1"
    local prefix="$2"
    shift 2
    local -a extra=("$@")

    # Skip if we already have this puzzle
    if has_puzzle "$OUTDIR" "$DATE" "$prefix"; then
        return
    fi

    # ${extra[@]+...} avoids "unbound variable" on bash 3.2 when array is empty
    local -a cmd=(xword-dl "$code" ${extra[@]+"${extra[@]}"} -o "$OUTDIR/%Y-%m-%d - %prefix - %title - %author")

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

download_latest() {
    # For sources that only support --latest (no -d DATE).
    # Their files are dated by publish date, not today, so we check the
    # whole month folder instead of anchoring to $DATE.
    local code="$1"
    local prefix="$2"

    if ls "$OUTDIR"/*.puz 2>/dev/null | grep -qF " - ${prefix} - "; then
        return
    fi

    local -a cmd=(xword-dl "$code" -o "$OUTDIR/%Y-%m-%d - %prefix - %title - %author")

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
download_latest bill  "Billboard"
download_latest vox   "Vox"
download vult  "Vulture"
download_latest db    "Daily Beast"
download_latest wal   "The Walrus"
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
clean_filenames "$OUTDIR" "$DATE"

# Count today's results
PUZZLES=$(find "$OUTDIR" -name "${DATE} -*\.puz" 2>/dev/null | wc -l | tr -d ' ')
log "Downloaded $PUZZLES puzzle(s) for $DATE"

echo "Downloaded $PUZZLES puzzle(s) for $DATE"
