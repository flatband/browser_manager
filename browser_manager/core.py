import logging
import random
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .user_agents import USER_AGENTS

logger = logging.getLogger(__name__)


@asynccontextmanager
async def browser_session(headless: bool = True):
    """Launch one Chromium browser for the life of this block.

    Create as many contexts as you like underneath it — each isolated,
    all sharing this one browser process. Browser and Playwright driver
    are guaranteed to close on exit, even on exception.

    Usage:
        async with browser_session() as browser:
            ctx1 = await new_context(browser)
            page1 = await new_page(ctx1)

            ctx2 = await new_context(browser)  # isolated from ctx1
            page2 = await new_page(ctx2)
    """
    playwright = await async_playwright().start()
    try:
        browser = await playwright.chromium.launch(headless=headless)
        logger.info("Browser launched.")
        try:
            yield browser
        finally:
            await browser.close()
            logger.info("Browser closed.")
    finally:
        await playwright.stop()
        logger.info("Playwright stopped.")


async def new_context(browser: Browser, user_agent: str | None = None) -> BrowserContext:
    """Create an isolated context: its own cookies, storage, cache.

    Pages opened from the same context share all of that.
    Pages from different contexts don't.
    """
    context = await browser.new_context(user_agent=user_agent or random.choice(USER_AGENTS))
    logger.debug("Context created.")
    return context


async def new_page(context: BrowserContext, default_timeout: int = 30) -> Page:
    """Open a new page inside an existing context. Set default timeout in seconds."""
    page = await context.new_page()
    if default_timeout:
        page.set_default_timeout(default_timeout*1000)
    logger.debug("Page created.")
    return page

async def reset_page(old_page: Page, context: BrowserContext, default_timeout: int = 30) -> Page:
    if not context: raise ValueError("Context is missing.")
    try:
        await old_page.close()
    except Exception:
        logger.warning("Couldn't dispose the old page.")
    return await new_page(context, default_timeout)