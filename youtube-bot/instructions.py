"""Instruction parser — converts user commands into bot actions.

Supported instruction types:
    visit <url>
    search <query>
    click_channel [<name>]
    go_to_videos
    watch <count> [duration=<seconds>]
    watch_video <url> [duration=<seconds>]
    like
    read_comments [<count>]
    subscribe
    scroll_down [<pixels>]
    wait <seconds>
    screenshot [<filename>]
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field


@dataclass
class Instruction:
    action: str
    args: dict = field(default_factory=dict)

    def __repr__(self):
        args_str = ", ".join(f"{k}={v!r}" for k, v in self.args.items())
        return f"Instruction({self.action}, {args_str})" if args_str else f"Instruction({self.action})"


def parse_duration(text: str) -> int | None:
    """Parse a duration string like '1m30s', '90', '90s', '2m'."""
    text = text.strip().lower()

    # Pure number → seconds
    if text.isdigit():
        return int(text)

    # Pattern: 1m30s or 1m or 30s
    m = re.match(r"(?:(\d+)m)?(?:(\d+)s)?$", text)
    if m and (m.group(1) or m.group(2)):
        minutes = int(m.group(1) or 0)
        seconds = int(m.group(2) or 0)
        return minutes * 60 + seconds

    return None


def parse_instruction(line: str) -> Instruction | None:
    """Parse a single instruction line into an Instruction object."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    parts = line.split(maxsplit=1)
    action = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""

    if action == "visit":
        url = rest.strip()
        if not url.startswith("http"):
            url = "https://" + url
        return Instruction("visit", {"url": url})

    elif action == "search":
        return Instruction("search", {"query": rest.strip()})

    elif action in ("click_channel", "channel"):
        return Instruction("click_channel", {"name": rest.strip() or None})

    elif action in ("go_to_videos", "videos"):
        return Instruction("go_to_videos")

    elif action == "watch":
        # watch 5 duration=90  OR  watch 5 duration=1m30s  OR  watch 5
        args: dict = {}
        tokens = rest.split()
        like_all = False
        read_comments = False

        for token in tokens:
            if token.isdigit():
                args["count"] = int(token)
            elif token.startswith("duration="):
                dur = parse_duration(token.split("=", 1)[1])
                if dur:
                    args["duration"] = dur
            elif token == "like":
                like_all = True
            elif token in ("comments", "read_comments"):
                read_comments = True

        args.setdefault("count", 1)
        args["like_all"] = like_all
        args["read_comments"] = read_comments
        return Instruction("watch", args)

    elif action == "watch_video":
        tokens = rest.split()
        url = tokens[0] if tokens else ""
        duration = None
        for token in tokens[1:]:
            if token.startswith("duration="):
                duration = parse_duration(token.split("=", 1)[1])
        return Instruction("watch_video", {"url": url, "duration": duration})

    elif action == "like":
        return Instruction("like")

    elif action in ("read_comments", "comments"):
        count = int(rest) if rest.strip().isdigit() else 10
        return Instruction("read_comments", {"count": count})

    elif action == "subscribe":
        return Instruction("subscribe")

    elif action in ("scroll_down", "scroll"):
        pixels = int(rest) if rest.strip().isdigit() else 500
        return Instruction("scroll_down", {"pixels": pixels})

    elif action == "wait":
        seconds = int(rest) if rest.strip().isdigit() else 5
        return Instruction("wait", {"seconds": seconds})

    elif action == "screenshot":
        filename = rest.strip() or "screenshot.png"
        return Instruction("screenshot", {"filename": filename})

    else:
        print(f"[Parser] Unknown instruction: {line}")
        return None


def parse_instructions(text: str) -> list[Instruction]:
    """Parse a multi-line instruction script into a list of Instructions."""
    instructions = []
    for line in text.strip().splitlines():
        inst = parse_instruction(line)
        if inst:
            instructions.append(inst)
    return instructions


def load_instructions_from_file(path: str) -> list[Instruction]:
    """Load and parse instructions from a text file."""
    with open(path) as f:
        return parse_instructions(f.read())
