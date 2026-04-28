"""
scraper/orchestrator.py
-----------------------
Tarama sürecini yöneten ana koordinatör. Listeleme sayfalarını tarar, ürün sayfalarını ziyaret eder ve Product nesneleri üretir.
Bağımlılık Ters Çevirme: somut I/O'ya değil, soyutlamalara (HttpClient, ayrıştırıcılar) bağlıdır.
"""

import logging
from typing import Iterator, Optional, Tuple

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
        already_saved_urls: Optional[set] = None,
    ):
        self.http = http_client
        self.listing_parser = listing_parser
        self.product_parser = product_parser
        self.max_pages = max_pages
        self.already_saved_urls = already_saved_urls or set()

    def scrape(self, start_url: str) -> Iterator[Tuple[Optional[Product], int]]:
        """
        Ürün nesnelerini tek tek veren bir jeneratör.
        Listeleme sayfalarını tarar ve her ürün URL'sini ziyaret eder.
        """
        current_url: Optional[str] = start_url
        pages_crawled = 0
        
        # URL'den mevcut sayfa numarasını çıkarmaya çalış
        current_page_num = 1
        if "/" in start_url:
            last_part = start_url.rstrip("/").split("/")[-1]
            if last_part.isdigit():
                current_page_num = int(last_part)

        while current_url:
            if self.max_pages and pages_crawled >= self.max_pages:
                logger.info("max_pages sınırına ulaşıldı (%d). Durduruluyor.", self.max_pages)
                break

            logger.info("Listeleme sayfası %d (Sitede: %d) çekiliyor: %s", pages_crawled + 1, current_page_num, current_url)

            html = self.http.get(current_url, wait_for="#products_match_all")
            
            if html is None:
                logger.error("Listeleme sayfası ALINAMADI: %s. Hata loglandı, devam edilmeye çalışılıyor...", current_url)
                logger.error("BİLGİ: Sayfa %d yüklenemedi. Atlanıyor.", current_page_num)
                
                # Manuel sonraki sayfa tahmini
                if "/facets/" in current_url:
                    parts = current_url.rstrip("/").split("/")
                    if parts[-1].isdigit():
                        parts[-1] = str(int(parts[-1]) + 1)
                        current_url = "/".join(parts)
                    else:
                        current_url = current_url.rstrip("/") + "/2"
                    current_page_num += 1
                    pages_crawled += 1
                    continue
                else:
                    break
            
            product_urls, next_page_url = self.listing_parser.parse(html)
            logger.info("%d ürün bulundu, sayfa %d (Sitede sayfa: %d).", len(product_urls), pages_crawled + 1, current_page_num)

            for product_url in product_urls:
                if product_url in self.already_saved_urls:
                    logger.debug("Ürün zaten kayıtlı, atlanıyor: %s", product_url)
                    # Boş bir nesne veya işaretçi yield edebiliriz ama main.py Product bekliyor.
                    # Aslında main.py'deki kontrolü burada yapmak daha iyi.
                    # Yield None yaparsak main.py onu atlar.
                    yield None, pages_crawled + 1
                    continue

                product = self._scrape_product(product_url)
                if product:
                    yield product, pages_crawled + 1

            pages_crawled += 1
            current_page_num += 1
            
            if next_page_url:
                current_url = next_page_url
            else:
                if "/facets/" in current_url:
                    parts = current_url.rstrip("/").split("/")
                    if parts[-1].isdigit():
                        parts[-1] = str(int(parts[-1]) + 1)
                        current_url = "/".join(parts)
                    else:
                        current_url = current_url.rstrip("/") + "/2"
                else:
                    current_url = None

        logger.info("Tarama tamamlandı. Toplam taranan sayfa: %d.", pages_crawled)

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