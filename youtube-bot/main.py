#!/usr/bin/env python3
"""YouTube Automation Bot — CLI entry point.

Usage:
    # Run from an instruction file
    python main.py --file instructions.txt

    # Run from inline instructions
    python main.py --run "visit www.youtube.com" "search mind and motivation" "click_channel" "videos" "watch 5 duration=90"

    # Interactive mode
    python main.py --interactive

    # Choose browser (chromium, firefox, webkit)
    python main.py --browser firefox --file instructions.txt
"""

import argparse
import asyncio
import sys

from bot_controller import BotController
from instructions import parse_instruction, parse_instructions, load_instructions_from_file


async def run_file(path: str, browser: str):
    """Load instructions from a file and execute them."""
    instructions = load_instructions_from_file(path)
    if not instructions:
        print("No valid instructions found in file.")
        return

    controller = BotController(browser_type=browser)
    try:
        await controller.start()
        await controller.run(instructions)
    finally:
        await controller.stop()


async def run_inline(commands: list[str], browser: str):
    """Execute instructions passed as CLI arguments."""
    instructions = []
    for cmd in commands:
        inst = parse_instruction(cmd)
        if inst:
            instructions.append(inst)

    if not instructions:
        print("No valid instructions provided.")
        return

    controller = BotController(browser_type=browser)
    try:
        await controller.start()
        await controller.run(instructions)
    finally:
        await controller.stop()


async def run_interactive(browser: str):
    """Interactive mode — type instructions one at a time."""
    controller = BotController(browser_type=browser)
    try:
        await controller.start()

        print("\n" + "=" * 60)
        print("YouTube Bot — Interactive Mode")
        print("=" * 60)
        print("Type instructions one per line. Type 'help' for commands.")
        print("Type 'quit' or 'exit' to stop.\n")

        while True:
            try:
                line = input("bot> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

            if not line:
                continue

            if line.lower() in ("quit", "exit", "q"):
                break

            if line.lower() == "help":
                _print_help()
                continue

            if line.lower() == "status":
                print(f"Videos watched: {controller.bot.videos_watched}")
                print(f"Current video: {controller.bot.current_video_title}")
                continue

            # Support multi-line paste (separated by ;)
            if ";" in line:
                sub_lines = [l.strip() for l in line.split(";") if l.strip()]
                instructions = []
                for sub in sub_lines:
                    inst = parse_instruction(sub)
                    if inst:
                        instructions.append(inst)
                if instructions:
                    await controller.run(instructions)
                continue

            inst = parse_instruction(line)
            if inst:
                await controller._execute(inst)

    finally:
        await controller.stop()


def _print_help():
    print("""
Available commands:
  visit <url>                     Navigate to a URL
  search <query>                  Search YouTube for a query
  click_channel [<name>]          Click a channel in search results
  go_to_videos                    Go to channel's Videos tab
  watch <count> [duration=<sec>] [like] [comments]
                                  Watch N videos from channel page
  watch_video <url> [duration=<sec>]
                                  Watch a specific video
  like                            Like the current video
  read_comments [<count>]         Read comments on current video
  subscribe                       Subscribe to current channel
  scroll_down [<pixels>]          Scroll the page down
  wait <seconds>                  Pause execution
  screenshot [<filename>]         Take a screenshot
  status                          Show session stats
  help                            Show this help
  quit / exit                     Stop the bot

Duration format: 90, 90s, 1m30s, 2m
Chain commands with ;  e.g.: visit www.youtube.com; search cats; watch 3

Example full session:
  visit www.youtube.com
  search mind and motivation
  click_channel mind and motivation
  go_to_videos
  watch 20 duration=1m30s
""")


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Automation Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --interactive
  python main.py --file my_instructions.txt
  python main.py --run "visit www.youtube.com" "search cats" "watch 5 duration=90"
  python main.py --browser firefox --interactive
        """,
    )
    parser.add_argument(
        "--file", "-f",
        help="Path to an instruction file",
    )
    parser.add_argument(
        "--run", "-r",
        nargs="+",
        help="Inline instructions to execute",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start in interactive mode",
    )
    parser.add_argument(
        "--browser", "-b",
        default="chromium",
        choices=["chromium", "firefox", "webkit"],
        help="Browser to use (default: chromium)",
    )

    args = parser.parse_args()

    if not any([args.file, args.run, args.interactive]):
        parser.print_help()
        print("\nHint: use --interactive to start typing commands.")
        sys.exit(1)

    if args.file:
        asyncio.run(run_file(args.file, args.browser))
    elif args.run:
        asyncio.run(run_inline(args.run, args.browser))
    elif args.interactive:
        asyncio.run(run_interactive(args.browser))


if __name__ == "__main__":
    main()
