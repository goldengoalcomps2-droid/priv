"""
Video Watcher Agent - Downloads YouTube videos, extracts frames,
and uses vision AI to produce a detailed visual description of
every aspect of the video.

This agent SEES the video for you. Run it locally on your machine
where you have internet access and an API key.

Output: A comprehensive Video Vision Report (JSON + text) containing:
- Frame-by-frame visual descriptions
- Scene transitions and timing
- Color palettes, lighting, effects
- Text/titles on screen
- Object and element inventory
- Camera movement and composition
- Sound/music analysis (via transcript)
- Complete recreation blueprint

Usage:
    python -m agent_team.agents.video_creator.watcher <youtube_url>

    # Or with specific API:
    python -m agent_team.agents.video_creator.watcher <url> --api claude
    python -m agent_team.agents.video_creator.watcher <url> --api openai
"""

import os
import sys
import json
import base64
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime


class VideoWatcher:
    """
    The bot that watches videos and reports exactly what it sees.

    Supports multiple vision AI backends:
    - Claude (Anthropic API) - best quality
    - OpenAI (GPT-4 Vision)
    - Local (just extracts frames for manual review)
    """

    def __init__(self, work_dir: str = None, api: str = "claude"):
        self.work_dir = Path(work_dir or os.path.expanduser("~/.agent_team/video_watcher"))
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.api = api  # "claude", "openai", or "local"

    def watch(self, url: str, frame_interval: int = 5, max_frames: int = 40) -> dict:
        """
        Watch a video and produce a complete visual report.

        Args:
            url: YouTube URL
            frame_interval: Seconds between frame captures
            max_frames: Maximum frames to analyse (controls API cost)

        Returns:
            Complete vision report dict
        """
        vid_id = self._get_vid_id(url)
        vid_dir = self.work_dir / vid_id
        vid_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"  VIDEO WATCHER AGENT - WATCHING VIDEO")
        print(f"{'='*60}")
        print(f"\n  URL: {url}")
        print(f"  API: {self.api}")
        print(f"  Frame interval: {frame_interval}s")

        # Step 1: Download
        print(f"\n  [1/5] Downloading video...")
        video_path, meta = self._download(url, vid_dir)
        title = meta.get("title", "Unknown")
        duration = meta.get("duration", 0)
        print(f"  ✓ Title: {title}")
        print(f"  ✓ Duration: {duration}s ({duration//60}m {duration%60}s)")

        # Step 2: Extract frames
        print(f"\n  [2/5] Extracting frames every {frame_interval}s...")
        frames = self._extract_frames(video_path, vid_dir, frame_interval, max_frames)
        print(f"  ✓ Extracted {len(frames)} frames")

        # Step 3: Extract audio info
        print(f"\n  [3/5] Extracting audio...")
        audio_info = self._extract_audio(video_path, vid_dir)
        print(f"  ✓ Audio: {audio_info.get('status', 'done')}")

        # Step 4: Analyse frames with vision AI
        print(f"\n  [4/5] Analysing frames with vision AI ({self.api})...")
        frame_analyses = self._analyse_frames(frames, title, duration)
        print(f"  ✓ Analysed {len(frame_analyses)} frames")

        # Step 5: Compile report
        print(f"\n  [5/5] Compiling vision report...")
        report = self._compile_report(
            url=url,
            meta=meta,
            frames=frames,
            frame_analyses=frame_analyses,
            audio_info=audio_info,
        )

        # Save report
        report_json_path = vid_dir / "vision_report.json"
        report_text_path = vid_dir / "vision_report.txt"

        report_json_path.write_text(json.dumps(report, indent=2, default=str))
        report_text_path.write_text(self._format_text_report(report))

        print(f"\n{'='*60}")
        print(f"  WATCHING COMPLETE")
        print(f"{'='*60}")
        print(f"\n  Vision Report (JSON): {report_json_path}")
        print(f"  Vision Report (TXT):  {report_text_path}")
        print(f"  Frames directory:     {vid_dir / 'frames'}")
        print(f"\n  Feed the TXT report back to Claude to recreate the video.")
        print()

        return report

    def _get_vid_id(self, url: str) -> str:
        """Extract video ID from URL."""
        import re
        match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
        if match:
            return match.group(1)
        return hashlib.md5(url.encode()).hexdigest()[:11]

    def _download(self, url: str, vid_dir: Path) -> tuple:
        """Download video and metadata."""
        video_path = vid_dir / "video.mp4"
        meta_path = vid_dir / "meta.json"

        # Get metadata
        meta = {}
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-download", url],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                meta = json.loads(result.stdout)
                meta_path.write_text(json.dumps(meta, indent=2))
        except Exception as e:
            print(f"  Warning: metadata extraction failed: {e}")

        # Download video
        if not video_path.exists():
            try:
                subprocess.run(
                    ["yt-dlp",
                     "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                     "--merge-output-format", "mp4",
                     "-o", str(video_path),
                     url],
                    capture_output=True, timeout=600
                )
            except Exception as e:
                print(f"  Warning: download failed: {e}")

        # If meta failed but video exists, try ffprobe
        if not meta and video_path.exists():
            try:
                result = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-print_format", "json",
                     "-show_format", "-show_streams", str(video_path)],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    probe = json.loads(result.stdout)
                    fmt = probe.get("format", {})
                    meta = {
                        "title": fmt.get("tags", {}).get("title", "Unknown"),
                        "duration": float(fmt.get("duration", 0)),
                    }
            except Exception:
                pass

        return video_path, meta

    def _extract_frames(self, video_path: Path, vid_dir: Path,
                        interval: int, max_frames: int) -> list:
        """Extract frames at regular intervals."""
        frames_dir = vid_dir / "frames"
        frames_dir.mkdir(exist_ok=True)

        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(video_path),
                 "-vf", f"fps=1/{interval},scale=1280:-1",
                 "-q:v", "2",
                 "-frames:v", str(max_frames),
                 str(frames_dir / "frame_%04d.jpg")],
                capture_output=True, timeout=120
            )
        except Exception as e:
            print(f"  Warning: frame extraction failed: {e}")

        frames = sorted(frames_dir.glob("frame_*.jpg"))
        return [
            {
                "path": str(f),
                "index": i,
                "timestamp": i * interval,
                "timestamp_str": f"{(i*interval)//60}:{(i*interval)%60:02d}",
            }
            for i, f in enumerate(frames)
        ]

    def _extract_audio(self, video_path: Path, vid_dir: Path) -> dict:
        """Extract and transcribe audio."""
        audio_path = vid_dir / "audio.wav"

        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(video_path),
                 "-vn", "-acodec", "pcm_s16le",
                 "-ar", "16000", "-ac", "1",
                 str(audio_path)],
                capture_output=True, timeout=120
            )
        except Exception:
            return {"status": "extraction_failed", "transcript": ""}

        # Try whisper transcription
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(str(audio_path))
            return {
                "status": "transcribed",
                "transcript": result.get("text", ""),
                "segments": [
                    {"start": s["start"], "end": s["end"], "text": s["text"]}
                    for s in result.get("segments", [])
                ],
                "language": result.get("language", "unknown"),
            }
        except ImportError:
            return {"status": "whisper_not_installed", "transcript": "Install: pip install openai-whisper"}
        except Exception as e:
            return {"status": f"transcription_failed: {e}", "transcript": ""}

    def _analyse_frames(self, frames: list, title: str, duration: float) -> list:
        """Send frames to vision AI for analysis."""
        if self.api == "local":
            return [{"frame": f["index"], "timestamp": f["timestamp_str"],
                      "description": f"[Frame at {f['timestamp_str']} - run with --api claude or --api openai for AI analysis]"}
                    for f in frames]

        analyses = []
        total = len(frames)

        for i, frame in enumerate(frames):
            print(f"    Analysing frame {i+1}/{total} ({frame['timestamp_str']})...", end="\r")

            try:
                with open(frame["path"], "rb") as f:
                    img_b64 = base64.b64encode(f.read()).decode()

                description = self._call_vision_api(
                    img_b64,
                    prompt=self._build_frame_prompt(frame, title, duration, i, total),
                )

                analyses.append({
                    "frame": frame["index"],
                    "timestamp": frame["timestamp_str"],
                    "timestamp_seconds": frame["timestamp"],
                    "description": description,
                    "path": frame["path"],
                })
            except Exception as e:
                analyses.append({
                    "frame": frame["index"],
                    "timestamp": frame["timestamp_str"],
                    "description": f"[Analysis failed: {e}]",
                })

        print(f"    Analysed {total}/{total} frames.          ")
        return analyses

    def _build_frame_prompt(self, frame: dict, title: str, duration: float,
                            idx: int, total: int) -> str:
        """Build the prompt for vision AI frame analysis."""
        return f"""You are a Video Watcher Agent. Analyse this frame from a YouTube video and describe EXACTLY what you see in precise detail. This description will be used to recreate this video in Blender and Premiere Pro.

Video: "{title}" | Frame {idx+1}/{total} | Timestamp: {frame['timestamp_str']} | Total duration: {duration}s

Describe ALL of the following:

1. SCENE: What is the setting/environment? Indoor/outdoor? Time of day?
2. OBJECTS: Every visible object, element, or character. Their positions, sizes, colors.
3. LIGHTING: Type (natural, artificial, ambient), direction, intensity, color temperature, shadows.
4. COLORS: Dominant color palette. Exact colors if possible (warm amber, cool blue, etc.).
5. COMPOSITION: Camera angle, framing, depth of field, perspective.
6. TEXT: Any text, titles, watermarks, or overlays visible.
7. EFFECTS: Any visual effects - particles, glow, fog, blur, grain, vignette, etc.
8. ANIMATION: Any visible motion or animated elements (compare to a still image).
9. STYLE: Is this 2D art, 3D render, real footage, pixel art, anime, etc.?
10. MOOD: The overall atmosphere and feeling this frame conveys.

Be extremely specific. Instead of "a room", say "a dimly lit Japanese-style room with tatami mats, a low wooden table, warm amber lighting from a paper lantern in the upper right, rain visible through a large window on the left."

Respond in a structured format."""

    def _call_vision_api(self, img_b64: str, prompt: str) -> str:
        """Call the vision AI API."""
        if self.api == "claude":
            return self._call_claude(img_b64, prompt)
        elif self.api == "openai":
            return self._call_openai(img_b64, prompt)
        else:
            return "[No API configured]"

    def _call_claude(self, img_b64: str, prompt: str) -> str:
        """Call Anthropic Claude API with vision."""
        try:
            import anthropic
        except ImportError:
            # Try with raw HTTP
            return self._call_claude_http(img_b64, prompt)

        client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return message.content[0].text

    def _call_claude_http(self, img_b64: str, prompt: str) -> str:
        """Call Claude API via raw HTTP (no SDK needed)."""
        import urllib.request

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return "[Set ANTHROPIC_API_KEY environment variable]"

        body = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }],
        }).encode()

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )

        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        return data["content"][0]["text"]

    def _call_openai(self, img_b64: str, prompt: str) -> str:
        """Call OpenAI GPT-4 Vision API."""
        import urllib.request

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            return "[Set OPENAI_API_KEY environment variable]"

        body = json.dumps({
            "model": "gpt-4o",
            "max_tokens": 1000,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    {"type": "text", "text": prompt},
                ],
            }],
        }).encode()

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )

        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]

    def _compile_report(self, url, meta, frames, frame_analyses, audio_info) -> dict:
        """Compile everything into a comprehensive vision report."""
        return {
            "report_type": "Video Vision Report",
            "generated_at": datetime.now().isoformat(),
            "source": {
                "url": url,
                "title": meta.get("title", "Unknown"),
                "channel": meta.get("channel", meta.get("uploader", "Unknown")),
                "duration": meta.get("duration", 0),
                "resolution": f"{meta.get('width', '?')}x{meta.get('height', '?')}",
                "fps": meta.get("fps", 30),
                "description": meta.get("description", ""),
                "tags": meta.get("tags", []),
            },
            "audio": audio_info,
            "frames_extracted": len(frames),
            "frame_analyses": frame_analyses,
            "summary": self._build_summary(frame_analyses),
        }

    def _build_summary(self, analyses: list) -> str:
        """Build a summary from all frame analyses."""
        if not analyses:
            return "No frames analysed."

        descs = [a.get("description", "") for a in analyses if a.get("description")]
        if not descs:
            return "No descriptions available."

        return f"Analysed {len(descs)} frames. See frame_analyses for detailed per-frame descriptions."

    def _format_text_report(self, report: dict) -> str:
        """Format report as human-readable text."""
        lines = [
            "=" * 70,
            "  VIDEO VISION REPORT",
            "=" * 70,
            "",
            f"  Title:      {report['source']['title']}",
            f"  URL:        {report['source']['url']}",
            f"  Channel:    {report['source']['channel']}",
            f"  Duration:   {report['source']['duration']}s",
            f"  Resolution: {report['source']['resolution']}",
            f"  FPS:        {report['source']['fps']}",
            f"  Frames:     {report['frames_extracted']}",
            "",
        ]

        if report.get("audio", {}).get("transcript"):
            lines.extend([
                "-" * 70,
                "  AUDIO / TRANSCRIPT",
                "-" * 70,
                "",
                f"  Language: {report['audio'].get('language', 'unknown')}",
                f"  {report['audio']['transcript'][:500]}",
                "",
            ])

        lines.extend([
            "-" * 70,
            "  FRAME-BY-FRAME ANALYSIS",
            "-" * 70,
            "",
        ])

        for analysis in report.get("frame_analyses", []):
            lines.extend([
                f"  [{analysis.get('timestamp', '?')}] Frame {analysis.get('frame', '?')}",
                f"  {'-' * 40}",
                f"  {analysis.get('description', 'No description')}",
                "",
            ])

        lines.extend([
            "=" * 70,
            "  HOW TO USE THIS REPORT",
            "=" * 70,
            "",
            "  Paste this entire report into Claude and ask it to:",
            "  1. Generate a Blender Python script to recreate this video",
            "  2. Generate a Premiere Pro project file",
            "  3. Create a shot-by-shot storyboard",
            "",
            "  The frame-by-frame descriptions give Claude everything",
            "  it needs to recreate the visual style, composition,",
            "  lighting, colors, and effects of the original video.",
            "",
        ])

        return "\n".join(lines)


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m agent_team.agents.video_creator.watcher <youtube_url> [options]")
        print("")
        print("Options:")
        print("  --api claude    Use Claude API for vision analysis (default)")
        print("  --api openai    Use OpenAI GPT-4V for vision analysis")
        print("  --api local     Just extract frames, no AI analysis")
        print("  --frames N      Seconds between frame captures (default: 5)")
        print("  --max N         Maximum frames to analyse (default: 40)")
        print("")
        print("Environment variables:")
        print("  ANTHROPIC_API_KEY  - Required for --api claude")
        print("  OPENAI_API_KEY     - Required for --api openai")
        print("")
        print("Examples:")
        print("  python -m agent_team.agents.video_creator.watcher https://youtube.com/watch?v=abc123")
        print("  python -m agent_team.agents.video_creator.watcher https://youtube.com/watch?v=abc123 --api openai")
        print("  python -m agent_team.agents.video_creator.watcher https://youtube.com/watch?v=abc123 --api local --frames 10")
        sys.exit(1)

    url = sys.argv[1]
    api = "claude"
    frame_interval = 5
    max_frames = 40

    if "--api" in sys.argv:
        idx = sys.argv.index("--api")
        if idx + 1 < len(sys.argv):
            api = sys.argv[idx + 1]

    if "--frames" in sys.argv:
        idx = sys.argv.index("--frames")
        if idx + 1 < len(sys.argv):
            frame_interval = int(sys.argv[idx + 1])

    if "--max" in sys.argv:
        idx = sys.argv.index("--max")
        if idx + 1 < len(sys.argv):
            max_frames = int(sys.argv[idx + 1])

    watcher = VideoWatcher(api=api)
    report = watcher.watch(url, frame_interval=frame_interval, max_frames=max_frames)


if __name__ == "__main__":
    main()
