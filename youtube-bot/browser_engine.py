"""Core browser automation engine using Playwright."""

import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from config import BROWSER_TYPE, HEADLESS, SLOW_MO, PAGE_LOAD_TIMEOUT, NAVIGATION_TIMEOUT


class BrowserEngine:
    """Manages the browser lifecycle and provides low-level browser controls."""

    def __init__(self, browser_type=None, headless=None):
        self.browser_type = browser_type or BROWSER_TYPE
        self.headless = headless if headless is not None else HEADLESS
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    async def start(self):
        """Launch the browser and create a new page."""
        self._playwright = await async_playwright().start()

        launcher = getattr(self._playwright, self.browser_type)
        self._browser = await launcher.launch(
            headless=self.headless,
            slow_mo=SLOW_MO,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--start-maximized",
            ] if self.browser_type == "chromium" else [],
        )

        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )

        # Remove webdriver flag to avoid detection
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

        self._page = await self._context.new_page()
        self._page.set_default_timeout(PAGE_LOAD_TIMEOUT)
        self._page.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
        print(f"[BrowserEngine] Launched {self.browser_type} browser")
        return self._page

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page

    async def navigate(self, url: str):
        """Navigate to a URL."""
        print(f"[BrowserEngine] Navigating to {url}")
        await self.page.goto(url, wait_until="domcontentloaded")
        await asyncio.sleep(2)

    async def click(self, selector: str, timeout: int = 10000):
        """Click an element by selector."""
        await self.page.wait_for_selector(selector, timeout=timeout)
        await self.page.click(selector)

    async def type_text(self, selector: str, text: str, delay: int = 50):
        """Type text into an input field."""
        await self.page.wait_for_selector(selector, timeout=10000)
        await self.page.click(selector)
        await self.page.fill(selector, "")
        await self.page.type(selector, text, delay=delay)

    async def press_key(self, key: str):
        """Press a keyboard key."""
        await self.page.keyboard.press(key)

    async def scroll_down(self, pixels: int = 500):
        """Scroll the page down."""
        await self.page.evaluate(f"window.scrollBy(0, {pixels})")
        await asyncio.sleep(1)

    async def scroll_to_element(self, selector: str):
        """Scroll an element into view."""
        element = await self.page.wait_for_selector(selector, timeout=10000)
        if element:
            await element.scroll_into_view_if_needed()
            await asyncio.sleep(1)

    async def wait_for(self, selector: str, timeout: int = 10000):
        """Wait for an element to appear."""
        return await self.page.wait_for_selector(selector, timeout=timeout)

    async def exists(self, selector: str, timeout: int = 3000) -> bool:
        """Check if an element exists on the page."""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    async def get_text(self, selector: str) -> str:
        """Get the text content of an element."""
        element = await self.page.wait_for_selector(selector, timeout=10000)
        if element:
            return (await element.text_content()) or ""
        return ""

    async def get_all_texts(self, selector: str, limit: int = 50) -> list[str]:
        """Get text content of all matching elements."""
        await asyncio.sleep(1)
        elements = await self.page.query_selector_all(selector)
        texts = []
        for el in elements[:limit]:
            text = await el.text_content()
            if text and text.strip():
                texts.append(text.strip())
        return texts

    async def screenshot(self, path: str = "screenshot.png"):
        """Take a screenshot."""
        await self.page.screenshot(path=path)
        print(f"[BrowserEngine] Screenshot saved to {path}")

    async def stop(self):
        """Close the browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        print("[BrowserEngine] Browser closed")
