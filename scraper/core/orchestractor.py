"""
scraper/core/orchestrator.py
-----------------------------
Tarama sürecini yöneten ana koordinatör (Asenkron).
Listeleme sayfalarını tarar, ürün sayfalarını ziyaret eder ve Product nesneleri üretir.

Bağımlılık Tersine Çevirme:
  - Somut PlaywrightClient'a değil, soyut BaseHttpClient'a bağlıdır.
  - Ayrıştırıcılar interface olarak enjekte edilir — test için kolayca değiştirilebilir.
"""

import asyncio
import logging
from typing import AsyncIterator, Optional, Tuple

from scraper.http.base import BaseHttpClient
from scraper.parsers.listing_parser import ListingParser
from scraper.parsers.product_parser import ProductParser
from models.product import Product

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """Listeleme → ürün URL toplama → ürün parse döngüsünü yönetir."""

    def __init__(
        self,
        http_client: BaseHttpClient,
        listing_parser: ListingParser,
        product_parser: ProductParser,
        max_pages: Optional[int] = None,
        already_saved_urls: Optional[set] = None,
    ):
        self.http = http_client
        self.listing_parser = listing_parser
        self.product_parser = product_parser
        self.max_pages = max_pages
        self.already_saved_urls = already_saved_urls or set()

    # ------------------------------------------------------------------ #
    # Ana giriş noktası
    # ------------------------------------------------------------------ #

    async def scrape(self, start_url: str) -> AsyncIterator[Tuple[Optional[Product], int]]:
        """
        Ürün nesnelerini tek tek veren asenkron bir jeneratör.
        Listeleme sayfalarını tarar ve her ürün URL'sini asenkron/paralel olarak ziyaret eder.

        Yields:
            (Product | None, page_number)  — None, atlanmış URL'yi temsil eder.
        """
        current_url: Optional[str] = start_url
        pages_crawled = 0
        current_page_num = self._extract_start_page(start_url)

        while current_url:
            if self.max_pages and pages_crawled >= self.max_pages:
                logger.info("max_pages sınırına ulaşıldı (%d). Durduruluyor.", self.max_pages)
                break

            logger.info(
                "Listeleme sayfası %d (Sitede: %d) çekiliyor: %s",
                pages_crawled + 1, current_page_num, current_url,
            )

            html = await self.http.get(current_url, wait_for="#products_match_all")

            if html is None:
                current_url, current_page_num, pages_crawled = self._handle_failed_page(
                    current_url, current_page_num, pages_crawled
                )
                continue

            product_urls, next_page_url = self.listing_parser.parse(html)
            logger.info(
                "%d ürün bulundu, sayfa %d (Sitede sayfa: %d).",
                len(product_urls), pages_crawled + 1, current_page_num,
            )

            # Ürünleri asenkron ve paralel olarak (yield ederek) tarama
            async for product_tuple in self._scrape_products(product_urls, pages_crawled):
                yield product_tuple

            pages_crawled += 1
            current_page_num += 1
            current_url = self._resolve_next_url(current_url, next_page_url)

        logger.info("Tarama tamamlandı. Toplam taranan sayfa: %d.", pages_crawled)

    # ------------------------------------------------------------------ #
    # Yardımcı metodlar
    # ------------------------------------------------------------------ #

    async def _scrape_products(
        self, product_urls: list, pages_crawled: int
    ) -> AsyncIterator[Tuple[Optional[Product], int]]:
        """Verilen URL listesindeki ürünleri paralel parse ederek yield eder."""
        sem = asyncio.Semaphore(8)

        async def _bounded_scrape(url: str) -> Optional[Product]:
            async with sem:
                return await self._scrape_single_product(url)

        tasks = []
        for product_url in product_urls:
            if product_url in self.already_saved_urls:
                logger.debug("Ürün zaten kayıtlı, atlanıyor: %s", product_url)
                # Anında yield ediyoruz (kayıtlı olduğu için None)
                yield None, pages_crawled + 1
                continue
            
            # Kayıtlı olmayanları task listesine at
            tasks.append(asyncio.create_task(_bounded_scrape(product_url)))

        # Paralel çalışan task'ları bitiş sırasına göre yakalayıp yield et
        for coro in asyncio.as_completed(tasks):
            product = await coro
            if product:
                yield product, pages_crawled + 1

    async def _scrape_single_product(self, url: str) -> Optional[Product]:
        html = await self.http.get(url, wait_for=None)
        if html is None:
            logger.warning("Ürün atlanıyor (çekme başarısız): %s", url)
            return None
        try:
            # HTML parse işlemi CPU-bound olduğu için senkron (await olmadan) çalışır.
            product = self.product_parser.parse(html, url)
            logger.debug("Ürün ayrıştırıldı: %s", product.name)
            return product
        except Exception:
            logger.warning("Ürün atlanıyor (ayrıştırma hatası): %s", url)
            return None

    def _handle_failed_page(
        self, current_url: str, current_page_num: int, pages_crawled: int
    ) -> Tuple[Optional[str], int, int]:
        """Sayfa yüklenemediğinde sonraki sayfayı tahmin eder."""
        logger.error("Listeleme sayfası ALINAMADI: %s", current_url)
        logger.error("BİLGİ: Sayfa %d yüklenemedi. Atlanıyor.", current_page_num)

        if "/facets/" in current_url:
            next_url = self._increment_page_in_url(current_url)
            return next_url, current_page_num + 1, pages_crawled + 1

        return None, current_page_num, pages_crawled

    def _resolve_next_url(self, current_url: str, next_page_url: Optional[str]) -> Optional[str]:
        """Sonraki sayfa URL'sini belirler; yoksa manuel olarak artırır."""
        if next_page_url:
            return next_page_url
        if "/facets/" in current_url:
            return self._increment_page_in_url(current_url)
        return None

    @staticmethod
    def _increment_page_in_url(url: str) -> str:
        """URL'nin son segmentini sayısal olarak artırır."""
        parts = url.rstrip("/").split("/")
        if parts[-1].isdigit():
            parts[-1] = str(int(parts[-1]) + 1)
        else:
            parts.append("2")
        return "/".join(parts)

    @staticmethod
    def _extract_start_page(url: str) -> int:
        """Başlangıç URL'sinden sayfa numarasını çıkarır."""
        if "/" in url:
            last_part = url.rstrip("/").split("/")[-1]
            if last_part.isdigit():
                return int(last_part)
        return 1