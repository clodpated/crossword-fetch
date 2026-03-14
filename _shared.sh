# _shared.sh — common functions for fetch-crosswords.sh and backfill.sh
#
# Source this file AFTER defining your own log() function.

has_puzzle() {
    # Check if a .puz file for this date+prefix already exists.
    # Uses fixed-string grep (-F) so prefix names are matched literally.
    local outdir="$1"
    local date="$2"
    local prefix="$3"
    ls "$outdir"/${date}*.puz 2>/dev/null | grep -qF " - ${prefix} - "
}

clean_filenames() {
    # Fill in Untitled/Unlisted for empty title/author tokens left by xword-dl.
    local outdir="$1"
    local date="$2"
    for f in "$outdir"/${date}*.puz; do
        [ -f "$f" ] || continue
        local name
        name=$(basename "$f")
        # Pattern: "date - prefix - TITLE - AUTHOR.puz"
        # Detect empty title (double dash) or trailing empty author
        local clean
        clean=$(echo "$name" | sed \
            's/\( - [^-]*\) - - \(.*\)\.puz/\1 - Untitled - \2.puz/' \
        )
        # If author is empty (trailing " - .puz")
        clean=$(echo "$clean" | sed 's/ - \.puz/ - Unlisted.puz/')
        # If both were empty, title is now "Untitled" but author might still be empty
        clean=$(echo "$clean" | sed 's/ - Untitled - \.puz/ - Untitled - Unlisted.puz/')
        if [ "$name" != "$clean" ]; then
            mv "$f" "$outdir/$clean"
            log "  Renamed → $clean"
        fi
    done
}
