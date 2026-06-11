"""
Browser connection management for Playwright.

Supports two modes:
  - CDP connection to an already-running Chromium instance (production tests)
  - Local browser launch (fallback / local development)
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from framework import config

if TYPE_CHECKING:
    from playwright.sync_api import Browser, Page, Playwright

logger = logging.getLogger(__name__)


def connect_or_launch(
    playwright: Playwright,
    *,
    debug_host: str = config.DEBUG_HOST,
    debug_port: int = config.DEBUG_PORT,
    headless: bool = config.HEADLESS,
    session_name: str = "browser",
) -> tuple[Browser, bool]:
    """
    Connect to a running browser via CDP, or launch a local one as fallback.

    Returns:
        (browser, owns_browser) — owns_browser is True when we launched it ourselves.
    """
    cdp_url = f"http://{debug_host}:{debug_port}"

    try:
        browser = playwright.chromium.connect_over_cdp(cdp_url)
        logger.info("Connected to %s via CDP at %s", session_name, cdp_url)
        return browser, False
    except Exception as exc:
        logger.warning(
            "CDP connection failed at %s: %s. Launching a local %s browser.",
            cdp_url, exc, session_name,
        )

    browser = playwright.chromium.launch(headless=headless)
    logger.info("Started local %s browser (headless=%s)", session_name, headless)
    return browser, True


def first_visible(scope, selectors: list[str], timeout: int = 3_000):
    """Try multiple selectors and return the first visible locator, or None."""
    for selector in selectors:
        locator = scope.locator(selector).first
        try:
            locator.wait_for(state="visible", timeout=timeout)
            return locator
        except Exception:
            continue
    return None


APP_URL_PATTERN = re.compile(rf"^{re.escape(config.APP_ADDRESS)}(?:/|$)")


def get_or_open_app_page(browser: Browser) -> Page:
    """Find an existing app page in the browser, or open a new one."""
    for ctx in browser.contexts:
        for page in ctx.pages:
            if APP_URL_PATTERN.match(page.url or ""):
                return page

    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(f"{config.APP_ADDRESS}/dashboard", wait_until="domcontentloaded", timeout=30_000)
    return page
