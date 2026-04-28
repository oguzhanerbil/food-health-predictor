"""
scraper/parsers/
----------------
HTML ayrıştırıcı katmanı.

Dışa aktarılanlar:
  ListingParser           → Listeleme sayfası ayrıştırıcısı
  ProductParser           → Ürün detay sayfası ayrıştırıcısı
  NutritionTableParser    → Beslenme tablosu (ProductParser tarafından kullanılır)
  NutrientMapper          → Label → NutritionFacts alan eşleyicisi
"""

from scraper.parsers.listing_parser import ListingParser
from scraper.parsers.product_parser import ProductParser

__all__ = ["ListingParser", "ProductParser"]