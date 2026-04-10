"""
Video Watcher Bot - Analyses YouTube videos LOCALLY. No API keys.

Downloads video, extracts frames, analyses each frame's colors,
lighting, composition, complexity, and scene changes using Pillow.
Outputs a text report you paste into Claude to recreate the video.

Usage:
    python3 watch_video.py <youtube_url>
    python3 watch_video.py <youtube_url> --frames 5 --max 30

The report prints to terminal AND saves to a file.
Copy-paste the report into Claude - that's it.
"""

from agent_team.agents.video_creator.watcher import main

if __name__ == "__main__":
    main()
