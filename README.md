# crossword-fetch

Automated daily `.puz` crossword puzzle downloader. A companion to [xword-dl](https://github.com/thisisparker/xword-dl) that orchestrates a full daily fetch across 20+ sources and fills gaps where xword-dl can't reach.

## What it does

- **`fetch-crosswords.sh`** — Runs daily (via cron, launchd, etc.), downloads puzzles from all sources into monthly folders (`~/Crosswords/2026-03/`). Uses a stamp file so it only downloads once per day even if triggered hourly.
- **`fetch-extras.py`** — Downloads puzzles that xword-dl can't reliably handle: Universal (API user-agent workaround), WSJ, and Universal Sunday.
- **`rename-library.py`** — Bulk-renames `.puz` files to a consistent human-readable format.

## Sources

| Source | Code | Handler | Notes |
|--------|------|---------|-------|
| New York Times | `nyt` | xword-dl | Requires NYT subscription |
| NY Times Mini | `nytm` | xword-dl | Requires NYT subscription |
| NY Times Midi | `nytd` | xword-dl | Requires NYT subscription; needs [PR #319](https://github.com/thisisparker/xword-dl/pull/319) |
| NY Times Variety | `nytv` | xword-dl | Requires NYT subscription |
| Los Angeles Times | `lat` | xword-dl | Free |
| LA Times Mini | `latm` | xword-dl | Free |
| USA Today | `usa` | xword-dl | Free |
| Universal | — | fetch-extras.py | xword-dl blocked by user-agent filter |
| Universal Sunday | — | fetch-extras.py | Not in xword-dl; via herbach.dnsalias.com |
| Wall Street Journal | — | fetch-extras.py | Not in xword-dl; via herbach.dnsalias.com |
| Newsday | `nd` | xword-dl | Free |
| Washington Post | `wp` | xword-dl | Free |
| Daily Pop | `pop` | xword-dl | Free |
| Puzzmo | `pzm` | xword-dl | Free |
| Puzzmo Big | `pzmb` | xword-dl | Free (weekly) |
| The New Yorker | `tny` | xword-dl | Free |
| New Yorker Mini | `tnym` | xword-dl | Free |
| The Atlantic | `atl` | xword-dl | Free |
| Billboard | `bill` | xword-dl | Free (latest only) |
| Vox | `vox` | xword-dl | Free (latest only) |
| Vulture | `vult` | xword-dl | Free |
| The Daily Beast | `db` | xword-dl | Free (latest only) |
| The Walrus | `wal` | xword-dl | Free (latest only) |
| Crossword Club | `club` | xword-dl | Free |

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- [xword-dl](https://github.com/thisisparker/xword-dl) — Install from git for the latest fixes:
  ```bash
  uv tool install --python 3.12 xword-dl --from 'git+https://github.com/thisisparker/xword-dl.git'
  ```
- NYT Games subscription (optional, for NYT puzzles)

## Quick start

1. **Clone the repo:**
   ```bash
   git clone https://github.com/clodpated/crossword-fetch.git
   cd crossword-fetch
   ```

2. **Configure NYT authentication** (optional):
   ```bash
   xword-dl nyt --authenticate
   ```
   Or manually add your `NYT-S` cookie to `~/.config/xword-dl/xword-dl.yaml`:
   ```yaml
   nyt:
     NYT_S: "your-cookie-value"
   ```

3. **Test it:**
   ```bash
   ./fetch-crosswords.sh
   ```
   Check `~/Crosswords/` for today's puzzles. The script finds `fetch-extras.py` relative to its own location, so both scripts must stay in the same directory.

4. **Schedule it** — pick your platform:

   **cron (Linux/macOS):**
   ```
   0 * * * * /path/to/crossword-fetch/fetch-crosswords.sh
   ```

   **launchd (macOS):** Edit `scheduling/com.crosswords.fetch.plist` with your paths, then:
   ```bash
   cp scheduling/com.crosswords.fetch.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.crosswords.fetch.plist
   ```

## Folder structure and filenames

Puzzles are organized into monthly folders with the date baked into each filename:

```
~/Crosswords/
├── 2026-01/
│   ├── 2026-01-01 - NY Times - Thursday, January 01, 2026 - Topher Booth.puz
│   ├── 2026-01-01 - Puzzmo - Blast Off! - Willa.puz
│   ├── 2026-01-01 - USA Today - Untitled - Unlisted.puz
│   └── ...
├── 2026-02/
├── 2026-03/
└── logs/
```

Filename format: `YYYY-MM-DD - Publisher - Title - Author.puz`

If a puzzle has no title in its metadata, `Untitled` is used. If no author, `Unlisted` (as in the USA Today example above).

## Renaming your library

If you have existing `.puz` files with different naming, `rename-library.py` can standardize them:

```bash
# Preview what would change
uv run --with puzpy python3 rename-library.py --dry-run

# Do it
uv run --with puzpy python3 rename-library.py
```

It reads each file's embedded metadata, maps source codes to publisher names, and renames everything to the standard format.

## Customizing

Edit `fetch-crosswords.sh` to add or remove sources from the `download` calls. Comment out any you don't want.

The `fetch-extras.py` script runs independently and can be called on its own:
```bash
uv run --with requests --with puzpy python3 fetch-extras.py --date 2026-03-13
```

## Gaps this fills

### NYT Midi

The NYT Midi crossword launched in early 2026 but isn't yet supported in a released version of xword-dl. This setup includes the `nytd` downloader from [PR #319](https://github.com/thisisparker/xword-dl/pull/319), which adds it as a subclass of the existing NYT downloader. If you install xword-dl from git (as recommended above), you can apply the patch manually — see the PR for the one-file change to `newyorktimesdownloader.py`.

### Universal, WSJ, Universal Sunday (fetch-extras.py)

Three sources need special handling that xword-dl doesn't provide:

- **Universal** — The AMUniversal API returns 403 to Python's default user-agent. `fetch-extras.py` sends a browser user-agent string. If the API fails, it falls back to downloading the raw `.puz` from herbach.dnsalias.com.
- **WSJ** — Not in xword-dl. Available as direct `.puz` downloads from herbach.dnsalias.com.
- **Universal Sunday** — Same as WSJ, published Sundays only.

## License

MIT
