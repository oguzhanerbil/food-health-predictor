"""
scraper/http/playwright_client.py
----------------------------------
Playwright tabanlı asenkron HTTP istemcisi. BaseHttpClient'ı uygular.
Özellikler: login desteği, retry mekanizması, rastgele gecikme.
"""

import asyncio
import random
import logging
from typing import Optional

from playwright.async_api import async_playwright

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
        
        # Asenkron nesneler start() metodu içinde oluşturulacak
        self.playwright = None
        self.browser = None
        self.page = None

    async def start(self) -> None:
        """Tarayıcıyı başlatır ve gerekli asenkron nesneleri oluşturur."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()

        if self.email and self.password:
            await self._login()

    async def __aenter__(self):
        """Asenkron context manager girişi."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asenkron context manager çıkışı."""
        await self.close()

    # ------------------------------------------------------------------ #
    # Login
    # ------------------------------------------------------------------ #

    async def _login(self) -> None:
        try:
            logger.info("OpenFoodFacts'e login yapılıyor: %s", self.email)

            login_url = "https://world.openfoodfacts.org/cgi/session.pl"
            await self.page.goto(login_url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            try:
                await self.page.fill("input[name='user_id']", self.email)
                await asyncio.sleep(0.5)
                await self.page.fill("input[name='password']", self.password)
                await asyncio.sleep(0.5)
                await self.page.click("input[type='submit'][name='submit']")
                logger.info("Alanlar dolduruldu: %s", self.email)
            except Exception as e:
                logger.warning("Field'lar bulunamadı: %s", e)
                return

            await asyncio.sleep(3)

            current_url = self.page.url
            logger.info("Callback URL: %s", current_url)

            if "oidc_signin_callback" in current_url.lower():
                logger.info("✓ Callback sayfasına ulaşıldı, session kurulduğu sırada...")
                await asyncio.sleep(2)

            logger.info("Ana sayfaya gidiyor...")
            await self.page.goto(
                "https://world.openfoodfacts.org/",
                timeout=self.timeout * 1000,
                wait_until="domcontentloaded",
            )
            await asyncio.sleep(2)

            final_url = self.page.url
            logger.info("Son URL: %s", final_url)

            try:
                logout_form = self.page.locator("form[action*='session.pl'] input[value='Sign out']")
                if await logout_form.count() > 0:
                    logger.info("Logout butonu bulundu")
                    return

                if (
                    await self.page.locator("a[href*='logout']").count() > 0
                    or await self.page.locator("text=/logout|Sign out/i").count() > 0
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

    async def get(self, url: str, wait_for: Optional[str] = "#products_match_all") -> Optional[str]:
        for attempt in range(1, self.retries + 1):
            try:
                await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))
                logger.info("GET %s (attempt %d/%d)", url, attempt, self.retries)

                await self.page.goto(url, timeout=self.timeout * 1000, wait_until="networkidle")
                await asyncio.sleep(2)

                # Selector bekleme — sadece liste sayfaları için
                if wait_for and "product/" not in url:
                    try:
                        logger.debug("Selector'ü bekleniyor: %s", wait_for)
                        await self.page.wait_for_selector(wait_for, timeout=10000)
                    except Exception as e:
                        logger.debug("Selector timeout, devam ediliyor: %s", e)
                        await asyncio.sleep(2)
                else:
                    try:
                        await self.page.wait_for_selector("h1, h2, [class*='product']", timeout=5000)
                    except Exception:
                        pass

                html = await self.page.content()

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
                    await asyncio.sleep(2)
                else:
                    logger.error("Maksimum deneme sayısına ulaşıldı")
                    return None

    async def close(self) -> None:
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()