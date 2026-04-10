"""
VideoCreatorAgent - Orchestrates the full pipeline:
  YouTube URL → Analyse → Blueprint → Blender Script + Premiere Project

Usage:
    from agent_team.agents.video_creator.agent import VideoCreatorAgent

    agent = VideoCreatorAgent()
    result = agent.process("https://youtube.com/watch?v=...")
    print(result["blender_script"])   # Path to .py file
    print(result["premiere_project"]) # Path to .xml file
    print(result["blueprint"])        # Full VideoBlueprint object
"""

import os
from pathlib import Path

from .analyser import VideoAnalyser, VideoBlueprint
from .blender_gen import BlenderScriptGen
from .premiere_gen import PremiereProjectGen


class VideoCreatorAgent:
    """
    End-to-end video analysis and recreation agent.

    Takes a YouTube URL, analyses the video structure,
    and generates production files for Blender and Premiere Pro.
    """

    def __init__(self, work_dir: str = None):
        self.work_dir = Path(work_dir or os.path.expanduser("~/.agent_team/video_work"))
        self.analyser = VideoAnalyser(str(self.work_dir))
        self.blender_gen = BlenderScriptGen()
        self.premiere_gen = PremiereProjectGen()

    def process(self, url: str, frame_interval: int = 5,
                transcribe: bool = True) -> dict:
        """
        Full pipeline: analyse a YouTube video and generate production files.

        Args:
            url: YouTube video URL
            frame_interval: Seconds between extracted frames (default: 5)
            transcribe: Whether to transcribe audio (default: True)

        Returns:
            dict with keys: blueprint, blender_script, premiere_project, output_dir
        """
        print(f"\n{'='*60}")
        print(f"  VIDEO CREATOR AGENT")
        print(f"{'='*60}")
        print(f"\n  URL: {url}")

        # Step 1: Analyse
        print(f"\n  [1/3] Analysing video...")
        blueprint = self.analyser.analyse(
            url,
            frame_interval=frame_interval,
            transcribe=transcribe,
        )
        print(f"  ✓ Title: {blueprint.title}")
        print(f"  ✓ Duration: {blueprint.duration_seconds}s")
        print(f"  ✓ Scenes detected: {len(blueprint.scenes)}")
        print(f"  ✓ Frames extracted: {len(blueprint.frame_paths)}")
        print(f"  ✓ Transcript: {len(blueprint.transcript)} chars")

        # Output directory
        import hashlib
        vid_id = hashlib.md5(url.encode()).hexdigest()[:10]
        output_dir = self.work_dir / vid_id / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 2: Generate Blender script
        print(f"\n  [2/3] Generating Blender Python script...")
        blender_path = self.blender_gen.generate(blueprint, str(output_dir))
        blueprint.blender_script_path = blender_path
        print(f"  ✓ Blender script: {blender_path}")

        # Step 3: Generate Premiere Pro project
        print(f"\n  [3/3] Generating Premiere Pro project...")
        premiere_path = self.premiere_gen.generate(blueprint, str(output_dir))
        blueprint.premiere_project_path = premiere_path
        print(f"  ✓ Premiere project: {premiere_path}")

        # Generate storyboard text file
        storyboard_path = self._generate_storyboard(blueprint, str(output_dir))
        blueprint.storyboard_path = storyboard_path

        # Save updated blueprint
        bp_path = self.work_dir / vid_id / "blueprint.json"
        blueprint.save(str(bp_path))

        print(f"\n{'='*60}")
        print(f"  COMPLETE - All files generated")
        print(f"{'='*60}")
        print(f"\n  Output directory: {output_dir}")
        print(f"  Blueprint:        {bp_path}")
        print(f"  Blender script:   {blender_path}")
        print(f"  Premiere project: {premiere_path}")
        print(f"  Storyboard:       {storyboard_path}")
        print()

        return {
            "blueprint": blueprint,
            "blender_script": blender_path,
            "premiere_project": premiere_path,
            "storyboard": storyboard_path,
            "output_dir": str(output_dir),
        }

    def _generate_storyboard(self, bp: VideoBlueprint, output_dir: str) -> str:
        """Generate a human-readable storyboard document."""
        lines = [
            f"STORYBOARD: {bp.title}",
            f"Source: {bp.source_url}",
            f"Channel: {bp.channel}",
            f"Duration: {bp.duration_seconds}s | Resolution: {bp.resolution} | FPS: {bp.fps}",
            f"Pacing: {bp.pacing.get('pace', 'unknown')} "
            f"(avg scene: {bp.pacing.get('avg_scene_duration', 0)}s)",
            "",
            "=" * 60,
            "SCENES",
            "=" * 60,
            "",
        ]

        for i, scene in enumerate(bp.scenes, 1):
            start = scene.get("start", 0)
            end = scene.get("end", 0)
            desc = scene.get("description", "No description")

            lines.append(f"SCENE {i} [{self._fmt_time(start)} - {self._fmt_time(end)}]")
            lines.append(f"  Duration: {end - start:.1f}s")
            lines.append(f"  Content: {desc[:200]}")

            frame_indices = scene.get("frame_indices", [])
            if frame_indices and bp.frame_paths:
                valid = [fi for fi in frame_indices if fi < len(bp.frame_paths)]
                if valid:
                    lines.append(f"  Reference frames: {', '.join(str(f) for f in valid[:5])}")

            lines.append("")

        if bp.transcript:
            lines.append("=" * 60)
            lines.append("FULL TRANSCRIPT")
            lines.append("=" * 60)
            lines.append("")
            lines.append(bp.transcript)
            lines.append("")

        lines.append("=" * 60)
        lines.append("STYLE NOTES")
        lines.append("=" * 60)
        lines.append("")
        lines.append(bp.style_notes or "No style notes generated")
        lines.append("")

        lines.append("=" * 60)
        lines.append("RECREATION INSTRUCTIONS")
        lines.append("=" * 60)
        lines.append("")
        lines.append("BLENDER:")
        lines.append(f"  1. Open Blender")
        lines.append(f"  2. Go to Scripting workspace")
        lines.append(f"  3. Open: {bp.blender_script_path}")
        lines.append(f"  4. Click Run Script")
        lines.append(f"  5. Customise text objects and add your media")
        lines.append(f"  6. Render: Render > Render Animation")
        lines.append("")
        lines.append("PREMIERE PRO:")
        lines.append(f"  1. Open Premiere Pro")
        lines.append(f"  2. File > Import > {bp.premiere_project_path}")
        lines.append(f"  3. Sequence and markers will be created")
        lines.append(f"  4. Replace placeholder clips with your footage")
        lines.append(f"  5. Adjust titles and transitions")
        lines.append("")

        path = Path(output_dir) / f"storyboard_{bp.title[:30].replace(' ', '_')}.txt"
        path.write_text("\n".join(lines))
        return str(path)

    def _fmt_time(self, seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"


def process_video(url: str, **kwargs) -> dict:
    """Convenience function - create agent and process a URL."""
    agent = VideoCreatorAgent()
    return agent.process(url, **kwargs)
