"""
scraper/parsers/nutrition_table_parser.py
------------------------------------------
Beslenme değerleri tablosunu parse eder.
Tek Sorumluluk: BeautifulSoup tablosu → NutritionFacts nesnesini doldurma.

ProductParser'dan ayrılma nedeni:
  - Dinamik sütun tespiti ve satır iterasyonu bağımsız olarak test edilebilir.
  - Gelecekte farklı tablo formatları eklenirse bu sınıf değişir, ProductParser değişmez.
"""

import re
import logging
from typing import Optional

from bs4 import BeautifulSoup, Tag

from models.product import NutritionFacts
from .nutrient_mapper import NutrientMapper

logger = logging.getLogger(__name__)


class NutritionTableParser:
    """Beslenme tablosundan verileri çıkarır ve NutritionFacts nesnesine yazar."""

    # Denenen panel ID'leri — öncelik sırasına göre
    PANEL_IDS = [
        "panel_nutrition_facts_table_content",
        "panel_nutrition_facts_table_with_input_sets_content",
    ]

    def __init__(self) -> None:
        self._mapper = NutrientMapper()

    def parse(self, soup: BeautifulSoup, nf: NutritionFacts) -> None:
        """
        İki tablo kaynağını dener:
          1. panel_nutrition_facts_table_content          (standart)
          2. panel_nutrition_facts_table_with_input_sets_content (detaylı, çok sütunlu)

        Her iki tabloda da "As sold for 100 g / 100 ml" sütununu dinamik olarak
        tespit eder — sütun sayısına göre doğru indexi seçer.
        """
        for panel_id in self.PANEL_IDS:
            panel = soup.find(id=panel_id)
            if not panel:
                continue
            table = panel.find("table")
            if not table:
                continue

            col_idx = self._find_per100g_column(table)
            self._extract_rows(table, col_idx, nf)
            break  # İlk bulunan tabloyu kullan

    # ------------------------------------------------------------------ #
    # Özel yardımcılar
    # ------------------------------------------------------------------ #

    def _find_per100g_column(self, table: Tag) -> int:
        """
        Tablo başlığından "As sold for 100 g / 100 ml" sütununun
        sıfır tabanlı indexini döndürür. Bulunamazsa 1 (varsayılan) döner.
        """
        thead = table.find("thead")
        if not thead:
            return 1

        headers = thead.find_all("th")
        for i, th in enumerate(headers):
            txt = th.get_text(" ", strip=True).lower()
            if (
                "100 g" in txt
                and "100 ml" in txt
                and "serving" not in txt
                and "packaging" not in txt
                and "estimate" not in txt
            ):
                return i

        return 1  # Varsayılan: ikinci sütun

    def _extract_rows(self, table: Tag, col_idx: int, nf: NutritionFacts) -> None:
        """
        Tablo satırlarını iterate eder.
        Her satır için sadece col_idx sütununu okur.
        "?" değerleri None olarak kaydedilir.
        """
        tbody = table.find("tbody")
        if not tbody:
            return

        for row in tbody.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) <= col_idx:
                continue

            label = cells[0].get_text(" ", strip=True).lower()
            label = re.sub(r"\s+", " ", label).strip()
            value_text = cells[col_idx].get_text(" ", strip=True)

            self._mapper.map(label, value_text, nf)