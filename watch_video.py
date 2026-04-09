"""
Watch a YouTube video and generate a complete visual report.
NO API KEYS NEEDED. All analysis runs locally.

Usage:
    python watch_video.py <youtube_url>

Requirements:
    pip install yt-dlp Pillow
    ffmpeg must be installed (apt install ffmpeg / brew install ffmpeg)
"""

from agent_team.agents.video_creator.watcher import main

if __name__ == "__main__":
    main()
