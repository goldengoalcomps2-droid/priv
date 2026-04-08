"""
Watch a YouTube video and generate a complete visual report.

This bot downloads the video, extracts frames, sends them to
a vision AI (Claude or OpenAI) to describe exactly what it sees,
and produces a report you can feed back to Claude to recreate the video.

Usage:
    python watch_video.py <youtube_url>
    python watch_video.py <youtube_url> --api claude
    python watch_video.py <youtube_url> --api openai
    python watch_video.py <youtube_url> --api local

Set your API key:
    export ANTHROPIC_API_KEY=sk-ant-...
    export OPENAI_API_KEY=sk-...
"""

from agent_team.agents.video_creator.watcher import main

if __name__ == "__main__":
    main()
