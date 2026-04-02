"""Bot controller — executes parsed instructions against the YouTube bot."""

import asyncio
from browser_engine import BrowserEngine
from youtube_actions import YouTubeBot
from instructions import Instruction


class BotController:
    """Runs a sequence of instructions using the YouTube bot."""

    def __init__(self, browser_type: str = "chromium"):
        self.engine = BrowserEngine(browser_type=browser_type)
        self.bot: YouTubeBot | None = None

    async def start(self):
        await self.engine.start()
        self.bot = YouTubeBot(self.engine)

    async def stop(self):
        await self.engine.stop()

    async def run(self, instructions: list[Instruction]):
        """Execute a list of instructions sequentially."""
        if not self.bot:
            await self.start()

        total = len(instructions)
        print(f"\n{'='*60}")
        print(f"[Bot] Executing {total} instruction(s)")
        print(f"{'='*60}\n")

        for i, inst in enumerate(instructions, 1):
            print(f"\n[Step {i}/{total}] {inst}")
            await self._execute(inst)

        print(f"\n{'='*60}")
        print(f"[Bot] All {total} instructions completed")
        print(f"[Bot] Videos watched this session: {self.bot.videos_watched}")
        print(f"{'='*60}\n")

    async def _execute(self, inst: Instruction):
        """Execute a single instruction."""
        action = inst.action
        args = inst.args

        if action == "visit":
            url = args["url"]
            if "youtube.com" in url:
                await self.bot.go_to_youtube()
            else:
                await self.engine.navigate(url)

        elif action == "search":
            await self.bot.search(args["query"])

        elif action == "click_channel":
            await self.bot.click_channel(args.get("name"))

        elif action == "go_to_videos":
            await self.bot.go_to_channel_videos()

        elif action == "watch":
            await self.bot.watch_channel_videos(
                max_videos=args.get("count", 1),
                duration=args.get("duration"),
                like_all=args.get("like_all", False),
                read_comments_on_each=args.get("read_comments", False),
            )

        elif action == "watch_video":
            await self.bot.watch_video(
                url=args["url"],
                duration=args.get("duration"),
            )

        elif action == "like":
            await self.bot.like_video()

        elif action == "read_comments":
            await self.bot.read_comments(max_comments=args.get("count", 10))

        elif action == "subscribe":
            await self.bot.subscribe_to_channel()

        elif action == "scroll_down":
            await self.engine.scroll_down(args.get("pixels", 500))

        elif action == "wait":
            seconds = args.get("seconds", 5)
            print(f"[Bot] Waiting {seconds}s...")
            await asyncio.sleep(seconds)

        elif action == "screenshot":
            await self.engine.screenshot(args.get("filename", "screenshot.png"))

        else:
            print(f"[Bot] Unknown action: {action}")
