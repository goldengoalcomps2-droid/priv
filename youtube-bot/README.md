# YouTube Automation Bot

A cross-browser YouTube automation bot built with [Playwright](https://playwright.dev/python/). Watch videos, skip ads, like, read comments, and more — all hands-free.

## Features

- **Easy-to-use GUI** — point-and-click control panel with action buttons and live log
- **Cross-browser** — works on Chromium, Firefox, and WebKit (Safari)
- **Hands-free video watching** — no mouse movement required
- **Automatic ad skipping** — detects and skips YouTube ads; waits out unskippable ones
- **Watch duration control** — set exact watch time per video (e.g. `1m30s`), ad time excluded
- **Batch watching** — watch up to 20 videos in one session
- **Like videos** — like individual videos or auto-like during batch watch
- **Read comments** — scroll to and read the comment section
- **Instruction scripts** — write instruction files to automate full sessions
- **Interactive mode** — type commands live in a REPL
- **Anti-detection** — removes webdriver flags, uses realistic user agent

## Installation

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install browser binaries (one-time)
playwright install
```

## Quick Start

### Easiest: Graphical Interface (recommended)

```bash
python3 gui.py
```

Opens a control panel where you can:
- Click buttons to add commands (Visit YouTube, Search, Watch, Like, etc.)
- Edit the script directly in the editor
- Press **▶ Run Script** and watch the live log
- Save and load instruction scripts
- Switch between Chromium / Firefox / WebKit

### Run from an instruction file

```bash
python main.py --file example_instructions.txt
```

### Interactive mode

```bash
python main.py --interactive
```

### Inline commands

```bash
python main.py --run "visit www.youtube.com" "search mind and motivation" "click_channel" "go_to_videos" "watch 20 duration=1m30s"
```

### Choose a different browser

```bash
python main.py --browser firefox --interactive
python main.py --browser webkit --file example_instructions.txt
```

## Command Reference

| Command | Description |
|---|---|
| `visit <url>` | Navigate to a URL |
| `search <query>` | Search YouTube for a query |
| `click_channel [<name>]` | Click a channel in search results |
| `go_to_videos` | Navigate to channel's Videos tab |
| `watch <N> [duration=<time>] [like] [comments]` | Watch N videos from channel |
| `watch_video <url> [duration=<time>]` | Watch a specific video by URL |
| `like` | Like the current video |
| `read_comments [<count>]` | Read comments on current video |
| `subscribe` | Subscribe to current channel |
| `scroll_down [<pixels>]` | Scroll the page down |
| `wait <seconds>` | Pause execution |
| `screenshot [<filename>]` | Take a screenshot |

### Duration formats

- `90` — 90 seconds
- `90s` — 90 seconds
- `1m30s` — 1 minute 30 seconds
- `2m` — 2 minutes

## Example Instruction Files

### Basic: Watch channel videos

```
visit www.youtube.com
search mind and motivation
click_channel
go_to_videos
watch 20 duration=1m30s
```

### Watch, like, and read comments

```
visit www.youtube.com
search mind and motivation
click_channel
go_to_videos
watch 10 duration=1m30s like comments
```

### Watch a specific video

```
visit www.youtube.com
watch_video https://www.youtube.com/watch?v=VIDEO_ID duration=2m
like
read_comments 15
```

### Chain commands interactively

In interactive mode you can chain commands with `;`:

```
bot> visit www.youtube.com; search cats; watch 5 duration=60
```

## Configuration

Edit `config.py` to change defaults:

- `BROWSER_TYPE` — default browser (`chromium`, `firefox`, `webkit`)
- `HEADLESS` — run headless (must be `False` to watch videos)
- `DEFAULT_WATCH_DURATION` — default seconds per video (90)
- `MAX_VIDEOS_PER_SESSION` — hard cap on videos per session (20)
- `AD_CHECK_INTERVAL` — how often to check for ads during playback

## How Ad Skipping Works

1. Before each video plays, the bot checks for pre-roll ads
2. If a "Skip Ad" button appears, it clicks it immediately
3. If the ad is unskippable, it waits for the ad to finish (up to 30s)
4. During video playback, it checks for mid-roll ads every 2 seconds
5. Ad time is **not** counted toward your watch duration — you get the full time on actual content

## Notes

- You must be **logged into YouTube** in the browser if you want to like videos or subscribe. The bot opens a real browser window — log in manually the first time, and cookies will persist.
- The bot uses realistic browser fingerprints to avoid detection.
- YouTube's DOM can change over time. If selectors break, update them in `config.py`.
