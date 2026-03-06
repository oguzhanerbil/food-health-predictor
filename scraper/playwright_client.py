# scraper/playwright_client.py

import time
import random
import logging
from typing import Optional

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class PlaywrightClient:

    def __init__(
        self,
        min_delay: float = 1.5,
        max_delay: float = 4,
        timeout: int = 60,
        retries: int = 3,
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.timeout = timeout
        self.retries = retries
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()

    def get(self, url: str, wait_for: Optional[str] = "#products_match_all") -> Optional[str]:
        for attempt in range(1, self.retries + 1):
            try:
                time.sleep(random.uniform(self.min_delay, self.max_delay))
                logger.info("GET %s (attempt %d)", url, attempt)

                self.page.goto(url, timeout=self.timeout * 1000)

                if wait_for:
                    self.page.wait_for_selector(wait_for, timeout=self.timeout * 1000)

                html = self.page.content()

                with open("debug.html", "w", encoding="utf-8") as f:
                    f.write(html)

                return html

            except Exception as e:
                logger.warning("Sayfa yüklenemedi (attempt %d/%d): %s", attempt, self.retries, e)
                if attempt == self.retries:
                    return None

    def close(self):
        self.browser.close()
        self.playwright.stop()