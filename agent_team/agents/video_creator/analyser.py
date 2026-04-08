"""
Video Creator Agent - Analyses YouTube videos and generates production
scripts to recreate similar content in Blender and Premiere Pro.

Pipeline:
1. Download video + metadata from YouTube (yt-dlp)
2. Extract key frames at intervals (ffmpeg)
3. Transcribe audio to text (whisper)
4. Analyse video structure: scenes, transitions, effects, pacing
5. Generate a detailed Video Blueprint
6. Output Blender Python scripts (.py) for 3D/motion graphics
7. Output Premiere Pro project (XML) for editing assembly
"""

import os
import json
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field


@dataclass
class VideoBlueprint:
    """Complete analysis of a video for recreation."""
    source_url: str = ""
    title: str = ""
    channel: str = ""
    duration_seconds: float = 0
    resolution: str = ""
    fps: float = 0
    description: str = ""
    tags: list = field(default_factory=list)

    # Extracted data
    transcript: str = ""
    transcript_segments: list = field(default_factory=list)
    frame_paths: list = field(default_factory=list)
    frame_descriptions: list = field(default_factory=list)

    # Structural analysis
    scenes: list = field(default_factory=list)
    transitions: list = field(default_factory=list)
    effects: list = field(default_factory=list)
    music_cues: list = field(default_factory=list)
    text_overlays: list = field(default_factory=list)
    pacing: dict = field(default_factory=dict)
    color_palette: list = field(default_factory=list)
    style_notes: str = ""

    # Generation output paths
    blender_script_path: str = ""
    premiere_project_path: str = ""
    storyboard_path: str = ""

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()}

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, default=str))

    @classmethod
    def load(cls, path: str):
        data = json.loads(Path(path).read_text())
        return cls(**data)


class VideoAnalyser:
    """Downloads and analyses YouTube videos."""

    def __init__(self, work_dir: str = None):
        self.work_dir = Path(work_dir or os.path.expanduser("~/.agent_team/video_work"))
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def analyse(self, url: str, frame_interval: int = 5,
                transcribe: bool = True) -> VideoBlueprint:
        """Full analysis pipeline for a YouTube video."""
        bp = VideoBlueprint(source_url=url)

        # Step 1: Download video + metadata
        video_path, meta = self._download(url)
        bp.title = meta.get("title", "")
        bp.channel = meta.get("channel", "")
        bp.duration_seconds = meta.get("duration", 0)
        bp.description = meta.get("description", "")
        bp.tags = meta.get("tags", [])
        bp.fps = meta.get("fps", 30)
        bp.resolution = f"{meta.get('width', 1920)}x{meta.get('height', 1080)}"

        # Step 2: Extract key frames
        bp.frame_paths = self._extract_frames(video_path, frame_interval)

        # Step 3: Transcribe audio
        if transcribe:
            bp.transcript, bp.transcript_segments = self._transcribe(video_path)

        # Step 4: Analyse structure
        bp.scenes = self._detect_scenes(bp)
        bp.pacing = self._analyse_pacing(bp)
        bp.style_notes = self._analyse_style(meta)

        # Save blueprint
        vid_id = meta.get("id", hashlib.md5(url.encode()).hexdigest()[:10])
        bp_path = self.work_dir / vid_id / "blueprint.json"
        bp.save(str(bp_path))

        return bp

    def _download(self, url: str) -> tuple:
        """Download video and extract metadata using yt-dlp."""
        vid_dir = self.work_dir / hashlib.md5(url.encode()).hexdigest()[:10]
        vid_dir.mkdir(parents=True, exist_ok=True)

        video_path = vid_dir / "video.mp4"
        meta_path = vid_dir / "meta.json"

        # Download metadata first
        try:
            result = subprocess.run(
                ["yt-dlp", "--dump-json", "--no-download", url],
                capture_output=True, text=True, timeout=60
            )
            meta = json.loads(result.stdout) if result.returncode == 0 else {}
        except Exception:
            meta = {}

        if meta:
            meta_path.write_text(json.dumps(meta, indent=2))

        # Download video (720p max to save space/time)
        if not video_path.exists():
            try:
                subprocess.run(
                    ["yt-dlp", "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]",
                     "--merge-output-format", "mp4",
                     "-o", str(video_path), url],
                    capture_output=True, timeout=300
                )
            except Exception as e:
                print(f"Download failed: {e}")

        return video_path, meta

    def _extract_frames(self, video_path: Path, interval: int = 5) -> list:
        """Extract frames at regular intervals using ffmpeg."""
        frames_dir = video_path.parent / "frames"
        frames_dir.mkdir(exist_ok=True)

        try:
            subprocess.run(
                ["ffmpeg", "-i", str(video_path),
                 "-vf", f"fps=1/{interval},scale=640:-1",
                 "-q:v", "3",
                 str(frames_dir / "frame_%04d.jpg")],
                capture_output=True, timeout=120
            )
        except Exception as e:
            print(f"Frame extraction failed: {e}")

        frames = sorted(frames_dir.glob("frame_*.jpg"))
        return [str(f) for f in frames]

    def _transcribe(self, video_path: Path) -> tuple:
        """Transcribe audio using whisper."""
        transcript = ""
        segments = []

        # Extract audio first
        audio_path = video_path.parent / "audio.wav"
        try:
            subprocess.run(
                ["ffmpeg", "-i", str(video_path),
                 "-vn", "-acodec", "pcm_s16le",
                 "-ar", "16000", "-ac", "1",
                 str(audio_path)],
                capture_output=True, timeout=120
            )
        except Exception:
            return transcript, segments

        # Try whisper
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(str(audio_path))
            transcript = result.get("text", "")
            segments = [
                {
                    "start": s["start"],
                    "end": s["end"],
                    "text": s["text"],
                }
                for s in result.get("segments", [])
            ]
        except ImportError:
            # Fallback: no whisper available
            transcript = "[Whisper not installed - run: pip install openai-whisper]"
        except Exception as e:
            transcript = f"[Transcription failed: {e}]"

        return transcript, segments

    def _detect_scenes(self, bp: VideoBlueprint) -> list:
        """Estimate scene boundaries from transcript segments and frame count."""
        scenes = []
        duration = bp.duration_seconds or 1
        num_frames = len(bp.frame_paths)

        if bp.transcript_segments:
            # Group segments into scenes (~15 second chunks)
            current_scene = {"start": 0, "texts": [], "frame_indices": []}
            scene_duration = 0

            for seg in bp.transcript_segments:
                current_scene["texts"].append(seg["text"])
                scene_duration = seg["end"] - current_scene["start"]

                if scene_duration >= 15:
                    current_scene["end"] = seg["end"]
                    current_scene["description"] = " ".join(current_scene["texts"]).strip()
                    frame_start = int((current_scene["start"] / duration) * num_frames)
                    frame_end = int((current_scene["end"] / duration) * num_frames)
                    current_scene["frame_indices"] = list(range(
                        min(frame_start, num_frames - 1),
                        min(frame_end + 1, num_frames)
                    ))
                    scenes.append(current_scene)
                    current_scene = {"start": seg["end"], "texts": [], "frame_indices": []}

            # Last scene
            if current_scene["texts"]:
                current_scene["end"] = duration
                current_scene["description"] = " ".join(current_scene["texts"]).strip()
                scenes.append(current_scene)
        else:
            # No transcript - estimate from duration
            scene_len = 15
            for i in range(0, int(duration), scene_len):
                scenes.append({
                    "start": i,
                    "end": min(i + scene_len, duration),
                    "description": f"Scene at {i}s-{min(i+scene_len, int(duration))}s",
                })

        return scenes

    def _analyse_pacing(self, bp: VideoBlueprint) -> dict:
        """Analyse video pacing from scene data."""
        scenes = bp.scenes
        if not scenes:
            return {"avg_scene_duration": 0, "total_scenes": 0, "pace": "unknown"}

        durations = [s.get("end", 0) - s.get("start", 0) for s in scenes]
        avg = sum(durations) / len(durations) if durations else 0

        pace = "slow"
        if avg < 8:
            pace = "fast"
        elif avg < 15:
            pace = "medium"

        return {
            "avg_scene_duration": round(avg, 1),
            "total_scenes": len(scenes),
            "pace": pace,
            "shortest_scene": round(min(durations), 1) if durations else 0,
            "longest_scene": round(max(durations), 1) if durations else 0,
        }

    def _analyse_style(self, meta: dict) -> str:
        """Generate style notes from metadata."""
        title = meta.get("title", "")
        desc = meta.get("description", "")
        tags = meta.get("tags", [])
        duration = meta.get("duration", 0)

        notes = []
        notes.append(f"Title style: {title}")

        if duration < 60:
            notes.append("Format: Short-form (< 1 min) - likely TikTok/Shorts style")
        elif duration < 300:
            notes.append("Format: Medium-form (1-5 min) - standard YouTube")
        elif duration < 900:
            notes.append("Format: Long-form (5-15 min) - in-depth content")
        else:
            notes.append("Format: Extended (15+ min) - documentary/tutorial style")

        if tags:
            notes.append(f"Tags: {', '.join(tags[:10])}")

        return "\n".join(notes)
