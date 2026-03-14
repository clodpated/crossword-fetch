# crossword-fetch

Automated daily `.puz` crossword puzzle downloader. A companion to [xword-dl](https://github.com/thisisparker/xword-dl) that orchestrates a full daily fetch across 20+ sources and fills gaps where xword-dl can't reach.

## What it does

- **`fetch-crosswords.sh`** — Runs hourly (via cron, launchd, etc.), downloads puzzles from all sources into monthly folders (`~/Crosswords/2026-03/`). Skips any source whose puzzle already exists, so repeated runs only fetch what's still missing.
- **`fetch-extras.py`** — Downloads puzzles that xword-dl can't reliably handle: Universal (API user-agent workaround), WSJ, and Universal Sunday.
- **`backfill.sh`** — Downloads historical puzzles for a date range. Skips anything already downloaded.
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
   If that doesn't work, you can manually grab the cookie from your browser:
   1. Log in to [nytimes.com/crosswords](https://www.nytimes.com/crosswords) with your NYT subscription
   2. Open Developer Tools (`F12` or `Cmd+Opt+I` / `Ctrl+Shift+I`)
   3. Go to the **Application** tab (Chrome/Edge) or **Storage** tab (Firefox)
   4. Under **Cookies**, select `https://www.nytimes.com`
   5. Find the cookie named `NYT-S` and copy its **Value**
   6. Add it to `~/.config/xword-dl/xword-dl.yaml`:
      ```yaml
      nyt:
        NYT_S: "your-cookie-value"
      ```

3. **Test it:**
   ```bash
   ./fetch-crosswords.sh
   ```
   Check `~/Crosswords/` for today's puzzles. The script finds `fetch-extras.py` relative to its own location, so both scripts must stay in the same directory.

4. **Schedule it** — see [Scheduling](#scheduling) below for cron, launchd, or systemd setup.

## Scheduling

The script is designed to run hourly. Each run skips sources whose puzzles have already been downloaded, so repeated runs only attempt what's still missing. This means you catch puzzles regardless of when each publisher drops theirs throughout the day.

### cron (Linux / macOS)

The simplest option. Open your crontab:

```bash
crontab -e
```

Add this line (update the path):

```
0 * * * * /path/to/crossword-fetch/fetch-crosswords.sh
```

This runs at the top of every hour. Output goes to `~/Crosswords/logs/YYYY-MM-DD.log`.

> **Tip:** If your machine might be off at midnight, hourly is better than a single daily run — the stamp file prevents duplicate downloads.

### launchd (macOS)

Better than cron on a Mac — launchd fires missed jobs after waking from sleep.

1. Edit `scheduling/com.crosswords.fetch.plist` and replace `/Users/YOURUSER/` with your actual home directory path in all three places.

2. Copy it into place and load it:
   ```bash
   cp scheduling/com.crosswords.fetch.plist ~/Library/LaunchAgents/
   launchctl load ~/Library/LaunchAgents/com.crosswords.fetch.plist
   ```

3. Verify it's loaded:
   ```bash
   launchctl list | grep crosswords
   ```

To unload later: `launchctl unload ~/Library/LaunchAgents/com.crosswords.fetch.plist`

### systemd timer (Linux)

Create two files:

**`~/.config/systemd/user/crossword-fetch.service`**
```ini
[Unit]
Description=Fetch daily crossword puzzles

[Service]
Type=oneshot
ExecStart=/path/to/crossword-fetch/fetch-crosswords.sh
```

**`~/.config/systemd/user/crossword-fetch.timer`**
```ini
[Unit]
Description=Run crossword-fetch hourly

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
systemctl --user daemon-reload
systemctl --user enable --now crossword-fetch.timer
```

Check status:
```bash
systemctl --user status crossword-fetch.timer
journalctl --user -u crossword-fetch.service -n 20
```

`Persistent=true` means systemd will run a missed job after boot, similar to launchd on macOS.

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

## Backfilling

To download puzzles for a range of past dates:

```bash
./backfill.sh --start 2026-01-01 --end 2026-03-01
```

This iterates day by day, downloading from all sources that support date-based fetching (17 xword-dl sources plus Universal, WSJ, and Universal Sunday via `fetch-extras.py`). It skips any date+source that already has a `.puz` file, so it's safe to re-run if interrupted.

Sources that only support `--latest` (Billboard, Daily Beast, Vox, The Walrus) are excluded — they can't fetch by date.

Progress is logged to `~/Crosswords/logs/backfill.log`.

> **Tip:** Backfilling months of puzzles takes a while. The script sleeps 1 second between downloads to avoid hammering servers. If it gets interrupted, just run it again — it picks up where it left off.

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
