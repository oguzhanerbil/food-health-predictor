"""
scraper/http/playwright_client.py
----------------------------------
Playwright tabanlı HTTP istemcisi. BaseHttpClient'ı uygular.
Özellikler: login desteği, retry mekanizması, rastgele gecikme.
"""

import time
import random
import logging
from typing import Optional

from playwright.sync_api import sync_playwright

from scraper.http.base import BaseHttpClient

logger = logging.getLogger(__name__)


class PlaywrightClient(BaseHttpClient):

    def __init__(
        self,
        min_delay: float = 1.5,
        max_delay: float = 4,
        timeout: int = 60,
        retries: int = 6,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.timeout = timeout
        self.retries = retries
        self.email = email
        self.password = password
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()

        if email and password:
            self._login()

    # ------------------------------------------------------------------ #
    # Login
    # ------------------------------------------------------------------ #

    def _login(self) -> None:
        try:
            logger.info("OpenFoodFacts'e login yapılıyor: %s", self.email)

            login_url = "https://world.openfoodfacts.org/cgi/session.pl"
            self.page.goto(login_url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
            time.sleep(2)

            try:
                self.page.fill("input[name='user_id']", self.email)
                time.sleep(0.5)
                self.page.fill("input[name='password']", self.password)
                time.sleep(0.5)
                self.page.click("input[type='submit'][name='submit']")
                logger.info("Alanlar dolduruldu: %s", self.email)
            except Exception as e:
                logger.warning("Field'lar bulunamadı: %s", e)
                return

            time.sleep(3)

            current_url = self.page.url
            logger.info("Callback URL: %s", current_url)

            if "oidc_signin_callback" in current_url.lower():
                logger.info("✓ Callback sayfasına ulaşıldı, session kurulduğu sırada...")
                time.sleep(2)

            logger.info("Ana sayfaya gidiyor...")
            self.page.goto(
                "https://world.openfoodfacts.org/",
                timeout=self.timeout * 1000,
                wait_until="domcontentloaded",
            )
            time.sleep(2)

            final_url = self.page.url
            logger.info("Son URL: %s", final_url)

            try:
                logout_form = self.page.locator(
                    "form[action*='session.pl'] input[value='Sign out']"
                )
                if logout_form.count() > 0:
                    logger.info("Logout butonu bulundu")
                    return

                if (
                    self.page.locator("a[href*='logout']").count() > 0
                    or self.page.locator("text=/logout|Sign out/i").count() > 0
                ):
                    logger.info("Logout linki bulundu")
                    return
            except Exception as check_err:
                logger.info("Login kontrolü sırasında hata: %s", check_err)

        except Exception as e:
            logger.warning("❌ Login hatası: %s", e)

    # ------------------------------------------------------------------ #
    # BaseHttpClient implementasyonu
    # ------------------------------------------------------------------ #

    def get(self, url: str, wait_for: Optional[str] = "#products_match_all") -> Optional[str]:
        for attempt in range(1, self.retries + 1):
            try:
                time.sleep(random.uniform(self.min_delay, self.max_delay))
                logger.info("GET %s (attempt %d/%d)", url, attempt, self.retries)

                self.page.goto(url, timeout=self.timeout * 1000, wait_until="networkidle")
                time.sleep(2)

                # Selector bekleme — sadece liste sayfaları için
                if wait_for and "product/" not in url:
                    try:
                        logger.debug("Selector'ü bekleniyor: %s", wait_for)
                        self.page.wait_for_selector(wait_for, timeout=10000)
                    except Exception as e:
                        logger.debug("Selector timeout, devam ediliyor: %s", e)
                        time.sleep(2)
                else:
                    try:
                        self.page.wait_for_selector("h1, h2, [class*='product']", timeout=5000)
                    except Exception:
                        pass

                html = self.page.content()

                with open("debug_latest.html", "w", encoding="utf-8") as f:
                    f.write(html)

                if "product/" in url:
                    if len(html) > 5000:
                        logger.debug("Ürün sayfası başarıyla yüklendi (%d byte)", len(html))
                    else:
                        logger.warning(
                            "Ürün sayfası çok kısa (%d byte) - eksik olabilir", len(html)
                        )
                else:
                    if "#products_match_all" in html or "products_match_all" in html:
                        logger.debug("Ürün konteyneri HTML'de bulundu")
                    else:
                        logger.warning(
                            "Ürün konteyneri HTML'de BULUNAMADI - sayfanın yanlış olabilir"
                        )

                return html

            except Exception as e:
                logger.warning("Sayfa yüklenemedi (attempt %d/%d): %s", attempt, self.retries, e)
                if attempt < self.retries:
                    time.sleep(2)
                else:
                    logger.error("Maksimum deneme sayısına ulaşıldı")
                    return None

    def close(self) -> None:
        self.browser.close()
        self.playwright.stop()