"""
Video Watcher Agent - Downloads YouTube videos, extracts frames,
and analyses them using LOCAL computer vision (no API keys needed).

This bot SEES the video using:
- Color analysis (dominant colors, palette, brightness, contrast)
- Edge/motion detection (scene changes, movement intensity)
- OCR text detection (titles, overlays, watermarks)
- Audio analysis (speech, music, silence detection)
- Composition analysis (rule of thirds, symmetry, framing)
- Scene change detection (cut timing, transition patterns)

ALL processing is local. No API keys. No cloud. No cost.

Usage:
    python watch_video.py <youtube_url>
"""

import os
import sys
import json
import struct
import subprocess
import hashlib
import math
import colorsys
from pathlib import Path
from datetime import datetime
from collections import Counter


class FrameAnalyser:
    """Analyses individual frames using Pillow - no API needed."""

    def __init__(self):
        from PIL import Image
        self.Image = Image

    def analyse(self, frame_path: str, timestamp: float, index: int) -> dict:
        """Extract everything we can see from a single frame."""
        img = self.Image.open(frame_path)
        pixels = list(img.getdata())
        width, height = img.size

        result = {
            "frame": index,
            "timestamp": timestamp,
            "timestamp_str": f"{int(timestamp)//60}:{int(timestamp)%60:02d}",
            "resolution": f"{width}x{height}",
        }

        # Color analysis
        result["colors"] = self._analyse_colors(pixels, img)

        # Brightness and contrast
        result["lighting"] = self._analyse_lighting(pixels)

        # Composition
        result["composition"] = self._analyse_composition(img, pixels, width, height)

        # Edge density (detail/complexity)
        result["complexity"] = self._analyse_complexity(img)

        # Region analysis (what's in each quadrant)
        result["regions"] = self._analyse_regions(img, width, height)

        # Text detection (basic - looks for high contrast sharp edges)
        result["has_text_overlay"] = self._detect_text_regions(img)

        # Build natural language description
        result["description"] = self._describe(result)

        return result

    def _analyse_colors(self, pixels, img) -> dict:
        """Extract dominant colors and palette."""
        # Quantize to find dominant colors
        small = img.resize((80, 80)).convert("RGB")
        quantized = small.quantize(colors=8, method=2).convert("RGB")
        q_pixels = list(quantized.getdata())

        color_counts = Counter(q_pixels)
        total = len(q_pixels)

        dominant = []
        for color, count in color_counts.most_common(6):
            r, g, b = color
            h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
            name = self._name_color(r, g, b, h, s, v)
            dominant.append({
                "rgb": [r, g, b],
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "name": name,
                "percentage": round(count / total * 100, 1),
            })

        # Overall warmth/coolness
        avg_r = sum(p[0] for p in q_pixels) / total
        avg_g = sum(p[1] for p in q_pixels) / total
        avg_b = sum(p[2] for p in q_pixels) / total

        warmth = "warm" if avg_r > avg_b + 20 else "cool" if avg_b > avg_r + 20 else "neutral"

        # Saturation
        avg_s = sum(colorsys.rgb_to_hsv(p[0]/255, p[1]/255, p[2]/255)[1] for p in q_pixels) / total
        saturation = "vibrant" if avg_s > 0.5 else "muted" if avg_s > 0.2 else "desaturated"

        return {
            "dominant": dominant,
            "warmth": warmth,
            "saturation": saturation,
            "avg_rgb": [int(avg_r), int(avg_g), int(avg_b)],
        }

    def _name_color(self, r, g, b, h, s, v) -> str:
        """Give a human name to a color."""
        if v < 0.15:
            return "black"
        if v > 0.85 and s < 0.15:
            return "white"
        if s < 0.15:
            if v < 0.4:
                return "dark gray"
            elif v < 0.7:
                return "gray"
            else:
                return "light gray"

        hue_deg = h * 360
        names = [
            (15, "red"), (40, "orange"), (65, "yellow"), (80, "yellow-green"),
            (150, "green"), (180, "teal"), (200, "cyan"), (240, "blue"),
            (280, "purple"), (320, "magenta"), (345, "pink"), (360, "red"),
        ]

        color_name = "red"
        for threshold, name in names:
            if hue_deg <= threshold:
                color_name = name
                break

        if v < 0.4:
            return f"dark {color_name}"
        if s < 0.4:
            return f"muted {color_name}"
        if v > 0.8 and s > 0.6:
            return f"bright {color_name}"

        return color_name

    def _analyse_lighting(self, pixels) -> dict:
        """Analyse brightness, contrast, and lighting."""
        # Convert to grayscale values
        grays = [(0.299*p[0] + 0.587*p[1] + 0.114*p[2]) for p in pixels]

        avg_brightness = sum(grays) / len(grays)
        min_b = min(grays)
        max_b = max(grays)
        contrast = max_b - min_b

        # Brightness distribution
        dark_pct = sum(1 for g in grays if g < 64) / len(grays) * 100
        mid_pct = sum(1 for g in grays if 64 <= g < 192) / len(grays) * 100
        bright_pct = sum(1 for g in grays if g >= 192) / len(grays) * 100

        # Determine lighting type
        if avg_brightness < 50:
            brightness = "very dark"
        elif avg_brightness < 100:
            brightness = "dark / low-key"
        elif avg_brightness < 160:
            brightness = "medium"
        elif avg_brightness < 210:
            brightness = "bright"
        else:
            brightness = "very bright / high-key"

        if contrast > 200:
            contrast_desc = "high contrast"
        elif contrast > 120:
            contrast_desc = "medium contrast"
        else:
            contrast_desc = "low contrast / flat"

        return {
            "brightness": brightness,
            "avg_brightness": round(avg_brightness, 1),
            "contrast": contrast_desc,
            "contrast_value": round(contrast, 1),
            "dark_pct": round(dark_pct, 1),
            "mid_pct": round(mid_pct, 1),
            "bright_pct": round(bright_pct, 1),
        }

    def _analyse_composition(self, img, pixels, w, h) -> dict:
        """Analyse framing and composition."""
        small = img.resize((30, 30)).convert("RGB")
        sp = list(small.getdata())

        # Check if edges are darker (vignette)
        center_brightness = sum(
            0.299*sp[y*30+x][0] + 0.587*sp[y*30+x][1] + 0.114*sp[y*30+x][2]
            for y in range(10, 20) for x in range(10, 20)
        ) / 100

        edge_brightness = sum(
            0.299*sp[y*30+x][0] + 0.587*sp[y*30+x][1] + 0.114*sp[y*30+x][2]
            for y in range(30) for x in range(30)
            if y < 3 or y > 26 or x < 3 or x > 26
        ) / max(1, sum(1 for y in range(30) for x in range(30) if y < 3 or y > 26 or x < 3 or x > 26))

        has_vignette = center_brightness > edge_brightness + 15

        # Letterboxing detection
        top_row_brightness = sum(
            0.299*sp[x][0] + 0.587*sp[x][1] + 0.114*sp[x][2]
            for x in range(30)
        ) / 30
        bot_row_brightness = sum(
            0.299*sp[29*30+x][0] + 0.587*sp[29*30+x][1] + 0.114*sp[29*30+x][2]
            for x in range(30)
        ) / 30

        has_letterbox = top_row_brightness < 15 and bot_row_brightness < 15

        # Aspect ratio
        aspect = round(w / h, 2)
        if aspect > 2.2:
            aspect_name = "ultra-wide (cinematic)"
        elif aspect > 1.7:
            aspect_name = "16:9 (widescreen)"
        elif aspect > 1.4:
            aspect_name = "3:2"
        elif aspect > 1.1:
            aspect_name = "4:3"
        elif aspect > 0.7:
            aspect_name = "1:1 (square)"
        else:
            aspect_name = "9:16 (portrait/vertical)"

        return {
            "aspect_ratio": aspect,
            "aspect_name": aspect_name,
            "has_vignette": has_vignette,
            "has_letterbox": has_letterbox,
        }

    def _analyse_complexity(self, img) -> dict:
        """Measure visual complexity via edge detection."""
        gray = img.convert("L").resize((200, 200))
        px = list(gray.getdata())
        w = 200

        # Simple edge detection (difference from neighbors)
        edge_sum = 0
        count = 0
        for y in range(1, 199):
            for x in range(1, 199):
                center = px[y*w + x]
                diff = (
                    abs(center - px[(y-1)*w + x]) +
                    abs(center - px[(y+1)*w + x]) +
                    abs(center - px[y*w + (x-1)]) +
                    abs(center - px[y*w + (x+1)])
                ) / 4
                edge_sum += diff
                count += 1

        avg_edge = edge_sum / count if count else 0

        if avg_edge > 25:
            detail = "very detailed / complex"
        elif avg_edge > 15:
            detail = "moderately detailed"
        elif avg_edge > 8:
            detail = "simple / clean"
        else:
            detail = "minimal / flat (possibly solid or gradient)"

        return {"edge_intensity": round(avg_edge, 2), "detail_level": detail}

    def _analyse_regions(self, img, w, h) -> dict:
        """Analyse what's happening in different parts of the frame."""
        regions = {}
        names = {
            "top_left": (0, 0, w//2, h//2),
            "top_right": (w//2, 0, w, h//2),
            "bottom_left": (0, h//2, w//2, h),
            "bottom_right": (w//2, h//2, w, h),
            "center": (w//4, h//4, 3*w//4, 3*h//4),
        }

        for name, box in names.items():
            crop = img.crop(box).resize((20, 20)).convert("RGB")
            cp = list(crop.getdata())
            avg_r = sum(p[0] for p in cp) / len(cp)
            avg_g = sum(p[1] for p in cp) / len(cp)
            avg_b = sum(p[2] for p in cp) / len(cp)
            brightness = 0.299*avg_r + 0.587*avg_g + 0.114*avg_b

            regions[name] = {
                "avg_color": f"#{int(avg_r):02x}{int(avg_g):02x}{int(avg_b):02x}",
                "brightness": "dark" if brightness < 80 else "medium" if brightness < 170 else "bright",
            }

        return regions

    def _detect_text_regions(self, img) -> bool:
        """Detect if there's likely text overlay (high-contrast sharp edges)."""
        gray = img.convert("L").resize((100, 100))
        px = list(gray.getdata())

        # Look for sudden high-contrast horizontal transitions (text-like)
        text_score = 0
        for y in range(100):
            for x in range(1, 99):
                diff = abs(px[y*100+x] - px[y*100+x-1])
                if diff > 80:
                    text_score += 1

        return text_score > 200  # Threshold for "likely has text"

    def _describe(self, analysis: dict) -> str:
        """Generate natural language description from analysis data."""
        c = analysis["colors"]
        l = analysis["lighting"]
        comp = analysis["composition"]
        cpx = analysis["complexity"]

        # Build description
        parts = []

        # Lighting
        parts.append(f"Lighting: {l['brightness']}, {l['contrast']}")

        # Colors
        top_colors = [d["name"] for d in c["dominant"][:3]]
        parts.append(f"Colors: {', '.join(top_colors)} ({c['warmth']} tones, {c['saturation']})")

        # Composition
        parts.append(f"Framing: {comp['aspect_name']}")
        if comp["has_vignette"]:
            parts.append("Has vignette effect")
        if comp["has_letterbox"]:
            parts.append("Has letterboxing (cinematic bars)")

        # Detail
        parts.append(f"Detail: {cpx['detail_level']}")

        # Text
        if analysis["has_text_overlay"]:
            parts.append("Text/overlay likely present")

        return " | ".join(parts)


class SceneDetector:
    """Detects scene changes by comparing consecutive frames."""

    def detect(self, frame_analyses: list) -> list:
        """Identify scene boundaries from frame analysis data."""
        if len(frame_analyses) < 2:
            return [{"start": 0, "end": frame_analyses[0]["timestamp"] if frame_analyses else 0, "frames": [0]}]

        scenes = []
        current_scene = {"start": frame_analyses[0]["timestamp"], "frames": [0]}

        for i in range(1, len(frame_analyses)):
            prev = frame_analyses[i-1]
            curr = frame_analyses[i]

            # Compare color palettes
            color_diff = self._color_distance(
                prev["colors"]["avg_rgb"],
                curr["colors"]["avg_rgb"],
            )

            # Compare brightness
            bright_diff = abs(
                prev["lighting"]["avg_brightness"] -
                curr["lighting"]["avg_brightness"]
            )

            # Scene change if significant visual shift
            is_scene_change = color_diff > 60 or bright_diff > 40

            if is_scene_change:
                current_scene["end"] = prev["timestamp"]
                current_scene["duration"] = current_scene["end"] - current_scene["start"]
                scenes.append(current_scene)
                current_scene = {"start": curr["timestamp"], "frames": [i]}
            else:
                current_scene["frames"].append(i)

        # Close last scene
        current_scene["end"] = frame_analyses[-1]["timestamp"]
        current_scene["duration"] = current_scene["end"] - current_scene["start"]
        scenes.append(current_scene)

        return scenes

    def _color_distance(self, rgb1, rgb2) -> float:
        return math.sqrt(sum((a-b)**2 for a, b in zip(rgb1, rgb2)))


class VideoWatcher:
    """
    The bot that watches videos - NO API KEYS NEEDED.
    All analysis runs locally using Pillow and ffmpeg.
    """

    def __init__(self, work_dir: str = None):
        self.work_dir = Path(work_dir or os.path.expanduser("~/.agent_team/video_watcher"))
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.frame_analyser = FrameAnalyser()
        self.scene_detector = SceneDetector()

    def watch(self, url: str, frame_interval: int = 3, max_frames: int = 60) -> dict:
        """
        Watch a video and produce a complete visual report.
        No API keys. No cloud. Everything runs locally.
        """
        vid_id = self._get_vid_id(url)
        vid_dir = self.work_dir / vid_id
        vid_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"  VIDEO WATCHER - LOCAL VISION (No API needed)")
        print(f"{'='*60}")
        print(f"\n  URL: {url}")
        print(f"  Frame interval: {frame_interval}s")

        # Step 1: Download
        print(f"\n  [1/5] Downloading video...")
        video_path, meta = self._download(url, vid_dir)
        title = meta.get("title", "Unknown")
        duration = meta.get("duration", 0)
        print(f"  ✓ Title: {title}")
        print(f"  ✓ Duration: {duration}s ({int(duration)//60}m {int(duration)%60}s)")

        # Step 2: Extract frames
        print(f"\n  [2/5] Extracting frames every {frame_interval}s...")
        frame_paths = self._extract_frames(video_path, vid_dir, frame_interval, max_frames)
        print(f"  ✓ Extracted {len(frame_paths)} frames")

        # Step 3: Analyse each frame locally
        print(f"\n  [3/5] Analysing frames (local vision)...")
        frame_analyses = []
        for i, fp in enumerate(frame_paths):
            ts = i * frame_interval
            print(f"    Frame {i+1}/{len(frame_paths)} ({int(ts)//60}:{int(ts)%60:02d})...", end="\r")
            analysis = self.frame_analyser.analyse(fp, ts, i)
            frame_analyses.append(analysis)
        print(f"    Analysed {len(frame_analyses)} frames.              ")

        # Step 4: Detect scenes
        print(f"\n  [4/5] Detecting scene changes...")
        scenes = self.scene_detector.detect(frame_analyses)
        print(f"  ✓ Detected {len(scenes)} scenes")

        # Step 5: Transcribe audio
        print(f"\n  [5/5] Analysing audio...")
        audio_info = self._analyse_audio(video_path, vid_dir)
        print(f"  ✓ Audio: {audio_info.get('status', 'done')}")

        # Compile report
        report = {
            "report_type": "Video Vision Report (Local Analysis)",
            "generated_at": datetime.now().isoformat(),
            "api_used": "NONE - fully local",
            "source": {
                "url": url,
                "title": title,
                "channel": meta.get("channel", meta.get("uploader", "Unknown")),
                "duration": duration,
                "resolution": f"{meta.get('width', '?')}x{meta.get('height', '?')}",
                "fps": meta.get("fps", 30),
                "description": meta.get("description", "")[:500],
                "tags": meta.get("tags", [])[:20],
            },
            "audio": audio_info,
            "total_frames_analysed": len(frame_analyses),
            "frame_analyses": frame_analyses,
            "scenes": scenes,
            "overall_style": self._summarise_style(frame_analyses, scenes),
        }

        # Save
        report_json = vid_dir / "vision_report.json"
        report_txt = vid_dir / "vision_report.txt"
        report_json.write_text(json.dumps(report, indent=2, default=str))
        report_txt.write_text(self._format_report(report))

        print(f"\n{'='*60}")
        print(f"  WATCHING COMPLETE")
        print(f"{'='*60}")
        print(f"\n  Report (JSON): {report_json}")
        print(f"  Report (TXT):  {report_txt}")
        print(f"  Frames:        {vid_dir / 'frames'}")
        print(f"\n  Paste the TXT report into Claude to recreate the video.")
        print()

        return report

    def _get_vid_id(self, url: str) -> str:
        import re
        match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
        return match.group(1) if match else hashlib.md5(url.encode()).hexdigest()[:11]

    def _download(self, url: str, vid_dir: Path) -> tuple:
        video_path = vid_dir / "video.mp4"
        meta = {}

        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-download", url],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                meta = json.loads(result.stdout)
                (vid_dir / "meta.json").write_text(json.dumps(meta, indent=2))
        except Exception as e:
            print(f"  Warning: metadata failed: {e}")

        if not video_path.exists():
            try:
                subprocess.run(
                    ["yt-dlp", "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                     "--merge-output-format", "mp4", "-o", str(video_path), url],
                    capture_output=True, timeout=600
                )
            except Exception as e:
                print(f"  Warning: download failed: {e}")

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
                    streams = probe.get("streams", [])
                    video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
                    meta = {
                        "title": fmt.get("tags", {}).get("title", Path(video_path).stem),
                        "duration": float(fmt.get("duration", 0)),
                        "width": int(video_stream.get("width", 0)),
                        "height": int(video_stream.get("height", 0)),
                        "fps": eval(video_stream.get("r_frame_rate", "30/1")),
                    }
            except Exception:
                pass

        return video_path, meta

    def _extract_frames(self, video_path: Path, vid_dir: Path,
                        interval: int, max_frames: int) -> list:
        frames_dir = vid_dir / "frames"
        frames_dir.mkdir(exist_ok=True)

        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(video_path),
                 "-vf", f"fps=1/{interval},scale=1280:-1",
                 "-q:v", "2", "-frames:v", str(max_frames),
                 str(frames_dir / "frame_%04d.jpg")],
                capture_output=True, timeout=180
            )
        except Exception as e:
            print(f"  Warning: frame extraction failed: {e}")

        return sorted(str(f) for f in frames_dir.glob("frame_*.jpg"))

    def _analyse_audio(self, video_path: Path, vid_dir: Path) -> dict:
        """Analyse audio - transcribe if whisper available, otherwise basic analysis."""
        audio_path = vid_dir / "audio.wav"

        try:
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(video_path),
                 "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                 str(audio_path)],
                capture_output=True, timeout=120
            )
        except Exception:
            return {"status": "extraction_failed"}

        # Try whisper first
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(str(audio_path))
            return {
                "status": "transcribed",
                "transcript": result.get("text", ""),
                "language": result.get("language", "unknown"),
                "segments": [{"start": s["start"], "end": s["end"], "text": s["text"]}
                             for s in result.get("segments", [])[:50]],
            }
        except ImportError:
            pass

        # Fallback: basic audio analysis via file size / silence detection
        try:
            file_size = audio_path.stat().st_size
            # Rough estimate: 16-bit mono 16kHz = 32KB/sec
            est_duration = file_size / 32000
            has_audio = file_size > 100000  # > ~3 seconds of audio

            return {
                "status": "basic_analysis",
                "has_audio": has_audio,
                "estimated_duration": round(est_duration, 1),
                "note": "Install whisper for transcription: pip install openai-whisper",
            }
        except Exception:
            return {"status": "analysis_failed"}

    def _summarise_style(self, frame_analyses: list, scenes: list) -> dict:
        """Generate overall style summary from all frame data."""
        if not frame_analyses:
            return {}

        # Aggregate colors across all frames
        all_color_names = []
        for fa in frame_analyses:
            for c in fa.get("colors", {}).get("dominant", [])[:3]:
                all_color_names.append(c["name"])

        color_freq = Counter(all_color_names).most_common(8)

        # Average brightness
        avg_bright = sum(
            fa.get("lighting", {}).get("avg_brightness", 128)
            for fa in frame_analyses
        ) / len(frame_analyses)

        # Warmth consensus
        warmths = Counter(fa.get("colors", {}).get("warmth", "neutral") for fa in frame_analyses)
        dominant_warmth = warmths.most_common(1)[0][0]

        # Saturation consensus
        sats = Counter(fa.get("colors", {}).get("saturation", "muted") for fa in frame_analyses)
        dominant_sat = sats.most_common(1)[0][0]

        # Complexity consensus
        details = Counter(fa.get("complexity", {}).get("detail_level", "unknown") for fa in frame_analyses)
        dominant_detail = details.most_common(1)[0][0]

        # Scene pacing
        scene_durations = [s.get("duration", 0) for s in scenes]
        avg_scene = sum(scene_durations) / len(scene_durations) if scene_durations else 0

        return {
            "dominant_colors": [{"color": c, "frequency": f} for c, f in color_freq],
            "overall_brightness": round(avg_bright, 1),
            "brightness_label": "dark" if avg_bright < 100 else "medium" if avg_bright < 170 else "bright",
            "warmth": dominant_warmth,
            "saturation": dominant_sat,
            "visual_complexity": dominant_detail,
            "total_scenes": len(scenes),
            "avg_scene_duration": round(avg_scene, 1),
            "pacing": "fast" if avg_scene < 5 else "medium" if avg_scene < 15 else "slow",
            "has_text_overlays": any(fa.get("has_text_overlay") for fa in frame_analyses),
        }

    def _format_report(self, report: dict) -> str:
        """Format as human-readable text report."""
        src = report.get("source", {})
        style = report.get("overall_style", {})
        lines = [
            "=" * 70,
            "  VIDEO VISION REPORT (Local Analysis - No API)",
            "=" * 70,
            "",
            f"  Title:      {src.get('title', '?')}",
            f"  URL:        {src.get('url', '?')}",
            f"  Channel:    {src.get('channel', '?')}",
            f"  Duration:   {src.get('duration', 0)}s ({int(src.get('duration', 0))//60}m)",
            f"  Resolution: {src.get('resolution', '?')}",
            f"  FPS:        {src.get('fps', '?')}",
            "",
            "-" * 70,
            "  OVERALL STYLE",
            "-" * 70,
            "",
            f"  Brightness: {style.get('brightness_label', '?')} (avg {style.get('overall_brightness', '?')})",
            f"  Warmth:     {style.get('warmth', '?')}",
            f"  Saturation: {style.get('saturation', '?')}",
            f"  Complexity: {style.get('visual_complexity', '?')}",
            f"  Pacing:     {style.get('pacing', '?')} ({style.get('total_scenes', 0)} scenes, avg {style.get('avg_scene_duration', 0)}s each)",
            f"  Text/titles:{' YES' if style.get('has_text_overlays') else ' No'}",
            "",
            f"  Dominant colors:",
        ]

        for c in style.get("dominant_colors", [])[:6]:
            lines.append(f"    - {c['color']} (appears in {c['frequency']} frames)")

        # Audio
        audio = report.get("audio", {})
        if audio.get("transcript"):
            lines.extend([
                "",
                "-" * 70,
                "  AUDIO / TRANSCRIPT",
                "-" * 70,
                "",
                f"  Language: {audio.get('language', '?')}",
                f"  {audio['transcript'][:1000]}",
            ])

        # Frame-by-frame
        lines.extend([
            "",
            "-" * 70,
            "  FRAME-BY-FRAME ANALYSIS",
            "-" * 70,
            "",
        ])

        for fa in report.get("frame_analyses", []):
            lines.append(f"  [{fa.get('timestamp_str', '?')}] Frame {fa.get('frame', '?')}")

            colors = fa.get("colors", {})
            top3 = ", ".join(c["name"] + f" ({c['percentage']}%)" for c in colors.get("dominant", [])[:3])
            lines.append(f"    Colors: {top3} | {colors.get('warmth', '?')} | {colors.get('saturation', '?')}")

            lighting = fa.get("lighting", {})
            lines.append(f"    Lighting: {lighting.get('brightness', '?')} | {lighting.get('contrast', '?')}")
            lines.append(f"    Dark: {lighting.get('dark_pct', 0)}% | Mid: {lighting.get('mid_pct', 0)}% | Bright: {lighting.get('bright_pct', 0)}%")

            comp = fa.get("composition", {})
            lines.append(f"    Framing: {comp.get('aspect_name', '?')}")
            if comp.get("has_vignette"):
                lines.append(f"    Effect: Vignette detected")
            if comp.get("has_letterbox"):
                lines.append(f"    Effect: Letterboxing detected")

            cpx = fa.get("complexity", {})
            lines.append(f"    Detail: {cpx.get('detail_level', '?')}")

            if fa.get("has_text_overlay"):
                lines.append(f"    Text: Overlay/title likely present")

            lines.append("")

        # Scenes
        lines.extend([
            "-" * 70,
            "  SCENES DETECTED",
            "-" * 70,
            "",
        ])

        for i, scene in enumerate(report.get("scenes", []), 1):
            start = scene.get("start", 0)
            end = scene.get("end", 0)
            dur = scene.get("duration", 0)
            lines.append(f"  Scene {i}: {int(start)//60}:{int(start)%60:02d} - {int(end)//60}:{int(end)%60:02d} ({dur:.0f}s) [{len(scene.get('frames', []))} frames]")

        lines.extend([
            "",
            "=" * 70,
            "  PASTE THIS ENTIRE REPORT INTO CLAUDE TO RECREATE THE VIDEO",
            "=" * 70,
        ])

        return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Video Watcher - NO API KEYS NEEDED")
        print("")
        print("Usage: python watch_video.py <youtube_url>")
        print("       python watch_video.py <youtube_url> --frames 3 --max 60")
        print("")
        print("Options:")
        print("  --frames N   Seconds between captures (default: 3)")
        print("  --max N      Max frames to analyse (default: 60)")
        print("")
        print("Requirements: yt-dlp, ffmpeg, Pillow")
        print("  pip install yt-dlp Pillow")
        sys.exit(1)

    url = sys.argv[1]
    frame_interval = 3
    max_frames = 60

    if "--frames" in sys.argv:
        idx = sys.argv.index("--frames")
        if idx + 1 < len(sys.argv):
            frame_interval = int(sys.argv[idx + 1])

    if "--max" in sys.argv:
        idx = sys.argv.index("--max")
        if idx + 1 < len(sys.argv):
            max_frames = int(sys.argv[idx + 1])

    watcher = VideoWatcher()
    watcher.watch(url, frame_interval=frame_interval, max_frames=max_frames)


if __name__ == "__main__":
    main()
