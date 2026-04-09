"""
Video Watcher Bot - Downloads a YouTube video, extracts frames,
and pushes them to your repo so Claude can see them directly.

Claude Code has built-in vision - it can look at images.
This bot just gets the frames in front of Claude's eyes.

Usage:
    python watch_video.py <youtube_url>
    python watch_video.py <youtube_url> --frames 5 --max 30

After running, the frames will be in agent_team/video_frames/<video_id>/
Tell Claude: "look at the frames in agent_team/video_frames/<video_id>/"
"""

import os
import sys
import json
import shutil
import subprocess
import hashlib
import re
from pathlib import Path


def get_vid_id(url):
    match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else hashlib.md5(url.encode()).hexdigest()[:11]


def yt_dlp_cmd():
    """Find yt-dlp: try binary first, fall back to python -m yt_dlp."""
    if shutil.which("yt-dlp"):
        return ["yt-dlp"]
    return [sys.executable, "-m", "yt_dlp"]


def main():
    if len(sys.argv) < 2:
        print("Video Watcher Bot")
        print("Downloads video, extracts frames for Claude to see.")
        print("")
        print("Usage: python watch_video.py <youtube_url>")
        print("       python watch_video.py <youtube_url> --frames 5 --max 30")
        print("")
        print("Requirements: yt-dlp, ffmpeg")
        print("  pip install yt-dlp")
        sys.exit(1)

    url = sys.argv[1]
    frame_interval = 5
    max_frames = 30

    if "--frames" in sys.argv:
        idx = sys.argv.index("--frames")
        if idx + 1 < len(sys.argv):
            frame_interval = int(sys.argv[idx + 1])

    if "--max" in sys.argv:
        idx = sys.argv.index("--max")
        if idx + 1 < len(sys.argv):
            max_frames = int(sys.argv[idx + 1])

    vid_id = get_vid_id(url)
    repo_root = Path(__file__).parent
    frames_dir = repo_root / "agent_team" / "video_frames" / vid_id
    frames_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"  VIDEO WATCHER BOT")
    print(f"{'='*60}")
    print(f"  URL: {url}")
    print(f"  Video ID: {vid_id}")

    # Step 1: Get metadata
    print(f"\n  [1/3] Getting video metadata...")
    meta = {}
    try:
        result = subprocess.run(
            [*yt_dlp_cmd(), "--dump-json", "--no-download", url],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            meta = json.loads(result.stdout)
            (frames_dir / "meta.json").write_text(json.dumps({
                "title": meta.get("title", ""),
                "channel": meta.get("channel", meta.get("uploader", "")),
                "duration": meta.get("duration", 0),
                "description": meta.get("description", "")[:1000],
                "tags": meta.get("tags", [])[:20],
                "width": meta.get("width", 0),
                "height": meta.get("height", 0),
                "fps": meta.get("fps", 30),
                "url": url,
            }, indent=2))
            print(f"  ✓ Title: {meta.get('title', '?')}")
            print(f"  ✓ Duration: {meta.get('duration', 0)}s")
    except Exception as e:
        print(f"  Warning: {e}")

    # Step 2: Download video
    print(f"\n  [2/3] Downloading video...")
    video_path = frames_dir / "video.mp4"
    if not video_path.exists():
        try:
            subprocess.run(
                [*yt_dlp_cmd(), "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
                 "--merge-output-format", "mp4",
                 "-o", str(video_path), url],
                capture_output=True, timeout=600
            )
            print(f"  ✓ Downloaded")
        except Exception as e:
            print(f"  ✗ Download failed: {e}")
            sys.exit(1)
    else:
        print(f"  ✓ Already downloaded")

    # Step 3: Extract frames
    print(f"\n  [3/3] Extracting frames every {frame_interval}s (max {max_frames})...")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path),
             "-vf", f"fps=1/{frame_interval},scale=1280:-1",
             "-q:v", "2", "-frames:v", str(max_frames),
             str(frames_dir / "frame_%04d.jpg")],
            capture_output=True, timeout=180
        )
    except Exception as e:
        print(f"  ✗ Frame extraction failed: {e}")
        sys.exit(1)

    frames = sorted(frames_dir.glob("frame_*.jpg"))
    print(f"  ✓ Extracted {len(frames)} frames")

    # Write index
    index = {
        "url": url,
        "video_id": vid_id,
        "title": meta.get("title", "Unknown"),
        "duration": meta.get("duration", 0),
        "frame_interval": frame_interval,
        "frames": [f.name for f in frames],
        "frames_dir": str(frames_dir),
    }
    (frames_dir / "index.json").write_text(json.dumps(index, indent=2))

    print(f"\n{'='*60}")
    print(f"  DONE - {len(frames)} frames ready for Claude")
    print(f"{'='*60}")
    print(f"\n  Frames saved to: {frames_dir}")
    print(f"\n  Next steps:")
    print(f"  1. git add {frames_dir.relative_to(repo_root)}")
    print(f"  2. git commit -m 'Add video frames for {vid_id}'")
    print(f"  3. git push")
    print(f"  4. Tell Claude: 'Look at the frames in agent_team/video_frames/{vid_id}/'")
    print()


if __name__ == "__main__":
    main()
