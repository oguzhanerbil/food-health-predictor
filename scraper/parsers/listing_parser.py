"""
scraper/parsers/listing_parser.py
----------------------------------
Bir ürün listeleme sayfasını ayrıştırır (örneğin, /facets/nutrition-grades/a).
Tek Sorumluluk: HTML → (product_urls, next_page_url)
"""

import logging
from typing import List, Optional, Tuple

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://world.openfoodfacts.org"


class ListingParser:
    """Listeleme sayfasından ürün URL'lerini ve sonraki sayfa bağlantısını çıkarır."""

    def parse(self, html: str) -> Tuple[List[str], Optional[str]]:
        """
        Returns:
            product_urls: mutlak ürün sayfası URL'lerinin listesi
            next_page_url: bir sonraki listeleme sayfasının mutlak URL'si veya None
        """
        soup = BeautifulSoup(html, "lxml")
        print(soup.title.string if soup else "No title found")  # Hata ayıklama için
        product_urls = self._extract_product_urls(soup)
        next_page_url = self._extract_next_page(soup)
        return product_urls, next_page_url

    # ------------------------------------------------------------------ #
    # Özel yardımcılar
    # ------------------------------------------------------------------ #

    def _extract_product_urls(self, soup: BeautifulSoup) -> List[str]:
        urls: List[str] = []

        container = soup.find("ul", id="products_match_all")
        if not container:
            container = soup.find("ul", class_="search_results")
        if not container:
            logger.warning("Ürün liste konteyneri sayfada bulunamadı.")
            return urls

        for li in container.find_all("li"):
            a_tag = li.find("a", class_="list_product_a")
            if a_tag and a_tag.get("href"):
                href = a_tag["href"]
                full_url = href if href.startswith("http") else BASE_URL + href
                urls.append(full_url)

        logger.debug("Liste sayfasında %d ürün URL'si bulundu.", len(urls))
        return urls

    def _extract_next_page(self, soup: BeautifulSoup) -> Optional[str]:
        pagination = soup.find("ul", id="pages")
        if not pagination:
            return None

        next_li = pagination.find("a", rel=lambda r: r and "next" in r)
        if next_li and next_li.get("href"):
            href = next_li["href"]
            return href if href.startswith("http") else BASE_URL + href

        # Alternatif: <a> metni "Next" olan bir bağlantıyı arayın
        for a in pagination.find_all("a"):
            if a.get_text(strip=True).lower() == "next":
                href = a["href"]
                return href if href.startswith("http") else BASE_URL + href

        return None