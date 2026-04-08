"""
Video Creator - CLI entry point.

Usage:
    python create_video.py <youtube_url>
    python create_video.py <youtube_url> --no-transcribe
    python create_video.py <youtube_url> --frames 10

This will:
1. Download and analyse the YouTube video
2. Generate a Blender Python script (.py)
3. Generate a Premiere Pro project (.xml)
4. Generate a storyboard document (.txt)
5. Save everything to ~/.agent_team/video_work/
"""

import sys
from agent_team.agents.video_creator.agent import VideoCreatorAgent


def main():
    if len(sys.argv) < 2:
        print("Usage: python create_video.py <youtube_url> [--no-transcribe] [--frames N]")
        print("")
        print("Examples:")
        print("  python create_video.py https://youtube.com/watch?v=abc123")
        print("  python create_video.py https://youtube.com/watch?v=abc123 --no-transcribe")
        print("  python create_video.py https://youtube.com/watch?v=abc123 --frames 10")
        sys.exit(1)

    url = sys.argv[1]
    transcribe = "--no-transcribe" not in sys.argv
    frame_interval = 5

    if "--frames" in sys.argv:
        idx = sys.argv.index("--frames")
        if idx + 1 < len(sys.argv):
            frame_interval = int(sys.argv[idx + 1])

    agent = VideoCreatorAgent()
    result = agent.process(url, frame_interval=frame_interval, transcribe=transcribe)

    print("\nGenerated files:")
    print(f"  Blender:   {result['blender_script']}")
    print(f"  Premiere:  {result['premiere_project']}")
    print(f"  Storyboard: {result['storyboard']}")
    print(f"  All files: {result['output_dir']}")


if __name__ == "__main__":
    main()
