"""YouTube-specific automation actions."""

import asyncio
from browser_engine import BrowserEngine
from config import (
    SELECTORS, DEFAULT_WATCH_DURATION, AD_CHECK_INTERVAL,
    ELEMENT_TIMEOUT, MAX_VIDEOS_PER_SESSION,
)


class YouTubeBot:
    """Automates YouTube interactions: search, watch, like, read comments, etc."""

    def __init__(self, engine: BrowserEngine):
        self.engine = engine
        self.videos_watched = 0
        self.current_video_title = ""

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _dismiss_popups(self):
        """Dismiss cookie banners, sign-in prompts, and other overlays."""
        # Try multiple rounds — YouTube can layer popups
        for _ in range(3):
            dismissed = False
            for sel in [SELECTORS["cookie_accept"], SELECTORS["dismiss_signin"]]:
                try:
                    if await self.engine.exists(sel, timeout=2000):
                        await self.engine.click(sel)
                        await asyncio.sleep(1.5)
                        dismissed = True
                except Exception:
                    pass

            # Also try clicking any "No thanks" or "Dismiss" text buttons
            for text in ["No thanks", "Dismiss", "Not now", "Skip trial"]:
                try:
                    btn = await self.engine.page.query_selector(f'button:has-text("{text}")')
                    if btn and await btn.is_visible():
                        await btn.click()
                        await asyncio.sleep(1)
                        dismissed = True
                except Exception:
                    pass

            if not dismissed:
                break

    async def _skip_ad(self) -> bool:
        """Attempt to skip a YouTube ad. Returns True if an ad was handled."""
        try:
            # Check if an ad is currently playing
            ad_visible = await self.engine.exists(SELECTORS["ad_overlay"], timeout=1000)
            if not ad_visible:
                ad_visible = await self.engine.exists(SELECTORS["ad_text"], timeout=1000)

            if ad_visible:
                print("    [Ad] Advertisement detected, waiting for skip button...")
                # Wait up to 15 seconds for the skip button to appear
                for _ in range(15):
                    try:
                        skip_btn = await self.engine.page.query_selector(
                            SELECTORS["skip_ad_button"]
                        )
                        if skip_btn and await skip_btn.is_visible():
                            await skip_btn.click()
                            print("    [Ad] Skipped advertisement")
                            await asyncio.sleep(1)
                            return True
                    except Exception:
                        pass
                    await asyncio.sleep(1)

                # If no skip button, wait for the ad to finish (max 30s)
                print("    [Ad] No skip button — waiting for ad to finish...")
                for _ in range(30):
                    if not await self.engine.exists(SELECTORS["ad_overlay"], timeout=500):
                        print("    [Ad] Advertisement finished")
                        return True
                    await asyncio.sleep(1)
            return False
        except Exception:
            return False

    async def _ensure_playing(self):
        """Make sure the video is playing (not paused)."""
        try:
            paused = await self.engine.page.evaluate("""
                () => {
                    const v = document.querySelector('video.html5-main-video');
                    return v ? v.paused : false;
                }
            """)
            if paused:
                # Click the play button or the video itself
                try:
                    await self.engine.click(SELECTORS["play_button"], timeout=2000)
                except Exception:
                    await self.engine.page.click("video.html5-main-video")
                await asyncio.sleep(1)
        except Exception:
            pass

    # ── Core Actions ────────────────────────────────────────────────────

    async def go_to_youtube(self):
        """Navigate to YouTube."""
        await self.engine.navigate("https://www.youtube.com")
        await asyncio.sleep(3)
        await self._dismiss_popups()
        # Wait for the page to be interactive
        await asyncio.sleep(2)
        await self._dismiss_popups()
        print("[YouTube] Opened YouTube")

    async def search(self, query: str):
        """Type a query into the YouTube search bar and submit."""
        print(f"[YouTube] Searching for: {query}")
        await self._dismiss_popups()

        # Try multiple selector strategies for the search input
        search_typed = False
        for selector in ['input#search', 'input[name="search_query"]', 'ytd-searchbox input', '#search-input input']:
            try:
                await self.engine.page.wait_for_selector(selector, timeout=5000, state="visible")
                await self.engine.page.click(selector)
                await self.engine.page.fill(selector, "")
                await self.engine.page.type(selector, query, delay=50)
                search_typed = True
                break
            except Exception:
                continue

        if not search_typed:
            # Last resort: click the search icon area to focus, then type
            print("[YouTube] Trying keyboard shortcut to focus search...")
            await self.engine.page.keyboard.press("/")
            await asyncio.sleep(1)
            await self.engine.page.keyboard.type(query, delay=50)

        await asyncio.sleep(0.5)

        # Submit the search
        try:
            await self.engine.page.keyboard.press("Enter")
        except Exception:
            await self.engine.click(SELECTORS["search_button"])

        await asyncio.sleep(4)
        await self._dismiss_popups()
        print(f"[YouTube] Search results loaded for: {query}")

    async def click_channel(self, channel_name: str | None = None):
        """Click on a channel from search results.

        If channel_name is provided, tries to match it. Otherwise clicks the
        first channel result.
        """
        print(f"[YouTube] Looking for channel: {channel_name or 'first result'}")
        await asyncio.sleep(2)

        if channel_name:
            # Try to find the channel by name in search results
            channel_elements = await self.engine.page.query_selector_all(
                SELECTORS["channel_name_search"]
            )
            for el in channel_elements:
                text = await el.text_content()
                if text and channel_name.lower() in text.lower():
                    await el.click()
                    await asyncio.sleep(3)
                    print(f"[YouTube] Opened channel: {text.strip()}")
                    return

        # Fallback: click the first channel link
        try:
            await self.engine.click(SELECTORS["channel_link"], timeout=5000)
        except Exception:
            # If no dedicated channel result, try clicking through a video
            # and then going to the channel from the video page
            links = await self.engine.page.query_selector_all(
                SELECTORS["channel_name_search"]
            )
            if links:
                await links[0].click()
            else:
                print("[YouTube] Could not find a channel in search results")
                return

        await asyncio.sleep(3)
        print("[YouTube] Opened channel page")

    async def go_to_channel_videos(self):
        """Click the 'Videos' tab on a channel page."""
        print("[YouTube] Navigating to channel Videos tab")
        try:
            await self.engine.click(SELECTORS["channel_videos_tab"], timeout=5000)
        except Exception:
            # Fallback: try text-based click
            try:
                await self.engine.page.click("text=Videos")
            except Exception:
                print("[YouTube] Could not find Videos tab, may already be on it")
        await asyncio.sleep(3)

    async def get_video_links(self, max_count: int = 20) -> list:
        """Collect video links from the current channel/page."""
        max_count = min(max_count, MAX_VIDEOS_PER_SESSION)
        print(f"[YouTube] Collecting up to {max_count} video links...")

        # Scroll to load more videos
        for _ in range(3):
            await self.engine.scroll_down(1000)
            await asyncio.sleep(1)

        links = []
        elements = await self.engine.page.query_selector_all(
            SELECTORS["channel_video_items"]
        )

        # Fallback selectors if the primary one didn't match
        if not elements:
            elements = await self.engine.page.query_selector_all(
                "a#video-title"
            )
        if not elements:
            elements = await self.engine.page.query_selector_all(
                "ytd-grid-video-renderer a#video-title"
            )

        for el in elements[:max_count]:
            href = await el.get_attribute("href")
            title = (await el.get_attribute("title")) or (await el.text_content()) or ""
            if href and "/watch" in href:
                full_url = href if href.startswith("http") else f"https://www.youtube.com{href}"
                links.append({"url": full_url, "title": title.strip()})

        print(f"[YouTube] Found {len(links)} videos")
        return links

    async def watch_video(self, url: str, duration: int | None = None, title: str = ""):
        """Navigate to a video and watch it for the specified duration.

        Handles ads automatically by skipping or waiting them out. The
        *duration* timer only counts actual video playback time (ads excluded).
        """
        watch_time = duration if duration is not None else DEFAULT_WATCH_DURATION
        self.current_video_title = title
        self.videos_watched += 1

        print(f"\n[YouTube] ▶ Video {self.videos_watched}: {title or url}")
        print(f"[YouTube]   Watch duration: {watch_time}s")

        await self.engine.navigate(url)
        await asyncio.sleep(3)
        await self._dismiss_popups()

        # Handle pre-roll ads
        await self._skip_ad()

        # Ensure video is playing
        await self._ensure_playing()

        # Watch loop — count only non-ad seconds
        elapsed = 0
        while elapsed < watch_time:
            # Check for mid-roll ads
            ad_found = await self._skip_ad()
            if ad_found:
                continue  # Don't count ad time

            await self._ensure_playing()
            await asyncio.sleep(AD_CHECK_INTERVAL)
            elapsed += AD_CHECK_INTERVAL

            # Progress indicator every 30 seconds
            if elapsed % 30 == 0 and elapsed > 0:
                print(f"    [Watch] {elapsed}s / {watch_time}s")

        print(f"[YouTube] ✓ Finished watching ({watch_time}s)")

    async def like_video(self):
        """Like the currently playing video."""
        print("[YouTube] Liking video...")
        try:
            like_btn = await self.engine.page.query_selector(SELECTORS["like_button"])
            if like_btn:
                aria = await like_btn.get_attribute("aria-pressed")
                if aria == "true":
                    print("[YouTube] Video is already liked")
                    return
                await like_btn.click()
                await asyncio.sleep(1)
                print("[YouTube] ✓ Liked the video")
            else:
                # Fallback: try broader selector
                await self.engine.page.click(
                    'ytd-menu-renderer button[aria-label*="like"]',
                    timeout=5000,
                )
                print("[YouTube] ✓ Liked the video (fallback)")
        except Exception as e:
            print(f"[YouTube] Could not like video: {e}")

    async def read_comments(self, max_comments: int = 10):
        """Scroll to the comments section and read comments."""
        print(f"[YouTube] Reading up to {max_comments} comments...")

        # Scroll down to load comments
        for _ in range(5):
            await self.engine.scroll_down(600)
            await asyncio.sleep(1.5)

        try:
            await self.engine.wait_for(SELECTORS["comments_section"], timeout=10000)
        except Exception:
            print("[YouTube] Comments section did not load")
            return []

        # Give comments time to render
        await asyncio.sleep(2)

        # Scroll more to load additional comments
        for _ in range(3):
            await self.engine.scroll_down(400)
            await asyncio.sleep(1)

        comments = []
        comment_elements = await self.engine.page.query_selector_all(
            SELECTORS["comment_content"]
        )
        author_elements = await self.engine.page.query_selector_all(
            SELECTORS["comment_author"]
        )

        for i in range(min(max_comments, len(comment_elements))):
            text = await comment_elements[i].text_content()
            author = ""
            if i < len(author_elements):
                author = await author_elements[i].text_content()
            if text and text.strip():
                comment = {"author": (author or "").strip(), "text": text.strip()}
                comments.append(comment)
                print(f"    [{comment['author']}]: {comment['text'][:100]}...")

        print(f"[YouTube] Read {len(comments)} comments")
        return comments

    async def subscribe_to_channel(self):
        """Click the subscribe button on the current page."""
        print("[YouTube] Subscribing to channel...")
        try:
            sub_btn = await self.engine.page.query_selector(
                'ytd-subscribe-button-renderer button'
            )
            if sub_btn:
                await sub_btn.click()
                await asyncio.sleep(1)
                print("[YouTube] ✓ Subscribed")
            else:
                print("[YouTube] Subscribe button not found")
        except Exception as e:
            print(f"[YouTube] Could not subscribe: {e}")

    async def watch_channel_videos(
        self,
        max_videos: int = 20,
        duration: int | None = None,
        like_all: bool = False,
        read_comments_on_each: bool = False,
    ):
        """Watch multiple videos from the current channel page.

        Args:
            max_videos: Maximum number of videos to watch (up to 20).
            duration: Seconds to watch each video (default from config).
            like_all: If True, like every video.
            read_comments_on_each: If True, read comments on each video.
        """
        videos = await self.get_video_links(max_videos)
        if not videos:
            print("[YouTube] No videos found on this channel")
            return

        total = min(len(videos), max_videos, MAX_VIDEOS_PER_SESSION)
        print(f"\n{'='*60}")
        print(f"[YouTube] Starting session: {total} videos, {duration or DEFAULT_WATCH_DURATION}s each")
        print(f"{'='*60}\n")

        for i, video in enumerate(videos[:total]):
            print(f"\n--- Video {i+1} of {total} ---")
            await self.watch_video(
                url=video["url"],
                duration=duration,
                title=video["title"],
            )

            if like_all:
                await self.like_video()

            if read_comments_on_each:
                await self.read_comments()

            # Brief pause between videos
            if i < total - 1:
                print("[YouTube] Moving to next video in 3s...")
                await asyncio.sleep(3)

        print(f"\n{'='*60}")
        print(f"[YouTube] Session complete — watched {total} videos")
        print(f"{'='*60}")
