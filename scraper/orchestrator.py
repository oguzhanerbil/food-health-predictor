"""
scraper/orchestrator.py
-----------------------
Tarama sürecini yöneten ana koordinatör. Listeleme sayfalarını tarar, ürün sayfalarını ziyaret eder ve Product nesneleri üretir.
Bağımlılık Ters Çevirme: somut I/O'ya değil, soyutlamalara (HttpClient, ayrıştırıcılar) bağlıdır.
"""

import logging
from typing import Iterator, Optional

from scraper.playwright_client import PlaywrightClient
from scraper.listing_parser import ListingParser
from scraper.product_parser import ProductParser
from models.product import Product

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    def __init__(
        self,
        http_client: PlaywrightClient,
        listing_parser: ListingParser,
        product_parser: ProductParser,
        max_pages: Optional[int] = None,
    ):
        self.http = http_client
        self.listing_parser = listing_parser
        self.product_parser = product_parser
        self.max_pages = max_pages

    def scrape(self, start_url: str) -> Iterator[Product]:
        """
        Ürün nesnelerini tek tek veren bir jeneratör.
        Listeleme sayfalarını tarar ve her ürün URL'sini ziyaret eder.
        """
        current_url: Optional[str] = start_url
        pages_crawled = 0

        while current_url:
            if self.max_pages and pages_crawled >= self.max_pages:
                logger.info("max_pages sınırına ulaşıldı (%d). Durduruluyor.", self.max_pages)
                break

            logger.info("Listeleme sayfası %d çekiliyor: %s", pages_crawled + 1, current_url)

            html = self.http.get(current_url, wait_for="#products_match_all")
            if html is None:
                logger.error("Listeleme sayfası alınamadı. Durduruluyor.")
                break
            # Parser artık HTML string alıyor
            product_urls, next_page_url = self.listing_parser.parse(html)
            logger.info("%d ürün bulundu, sayfa %d.", len(product_urls), pages_crawled + 1)

            for product_url in product_urls:
                product = self._scrape_product(product_url)
                if product:
                    yield product

            pages_crawled += 1
            current_url = next_page_url

        logger.info("Tarama tamamlandı. Toplam sayfa: %d.", pages_crawled)

    def _scrape_product(self, url: str) -> Optional[Product]:
        html = self.http.get(url, wait_for=None)

        if html is None:
            logger.warning("Ürün atlanıyor (çekme başarısız): %s", url)
            return None
        try:
            product = self.product_parser.parse(html, url)
            logger.debug("Ürün ayrıştırıldı: %s", product.name)
            return product
        except Exception as exc:
            logger.warning("Ürün atlanıyor (ayrıştırma hatası): %s", url)
            return None