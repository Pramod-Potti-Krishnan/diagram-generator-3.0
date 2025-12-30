"""
Playwright Base Renderer

Shared Playwright browser instance for JavaScript-based renderers.
Used by Frappe Gantt, Markmap, and Kanban renderers.
"""

import asyncio
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page
import logging

from .base_renderer import BaseRenderer

logger = logging.getLogger(__name__)


class PlaywrightRenderer(BaseRenderer):
    """
    Base class for renderers that use Playwright for screenshot capture.

    Provides shared browser instance management and common rendering patterns.
    """

    _browser: Optional[Browser] = None
    _playwright = None

    def __init__(self):
        super().__init__()

    async def _get_browser(self) -> Browser:
        """Get or create the shared browser instance."""
        if PlaywrightRenderer._browser is None or not PlaywrightRenderer._browser.is_connected():
            self.logger.info("Launching Playwright browser...")
            PlaywrightRenderer._playwright = await async_playwright().start()
            PlaywrightRenderer._browser = await PlaywrightRenderer._playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            self.logger.info("Playwright browser launched")
        return PlaywrightRenderer._browser

    async def _create_page(self, width: int, height: int) -> Page:
        """Create a new page with specified viewport."""
        browser = await self._get_browser()
        page = await browser.new_page()
        await page.set_viewport_size({"width": width, "height": height})
        return page

    async def _render_html_to_png(
        self,
        html: str,
        width: int,
        height: int,
        wait_for_selector: Optional[str] = None,
        wait_for_function: Optional[str] = None,
        extra_wait_ms: int = 300
    ) -> bytes:
        """
        Render HTML content to PNG using Playwright.

        Args:
            html: Complete HTML document string
            width: Viewport width
            height: Viewport height
            wait_for_selector: Optional CSS selector to wait for
            wait_for_function: Optional JavaScript function to wait for (e.g., "window.ready === true")
            extra_wait_ms: Additional wait time after conditions are met

        Returns:
            PNG bytes
        """
        page = await self._create_page(width, height)

        try:
            await page.set_content(html)

            # Wait for specific selector if provided
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=15000)

            # Wait for JavaScript condition if provided
            if wait_for_function:
                await page.wait_for_function(wait_for_function, timeout=15000)

            # Extra wait for any animations or layout settling
            if extra_wait_ms > 0:
                await page.wait_for_timeout(extra_wait_ms)

            # Capture screenshot
            png_bytes = await page.screenshot(type='png')
            self.logger.info(f"Screenshot captured: {len(png_bytes)} bytes")
            return png_bytes

        finally:
            await page.close()

    async def render(
        self,
        data: Dict[str, Any],
        width: int = 1800,
        height: int = 840,
        theme: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Override in subclasses."""
        raise NotImplementedError("Subclasses must implement render()")

    def get_supported_types(self) -> list:
        """Override in subclasses."""
        return []

    @classmethod
    async def close_browser(cls):
        """Close the shared browser instance."""
        if cls._browser:
            await cls._browser.close()
            cls._browser = None
        if cls._playwright:
            await cls._playwright.stop()
            cls._playwright = None
        logger.info("Playwright browser closed")

    async def close(self):
        """Close browser resources."""
        await self.close_browser()
