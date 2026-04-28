"""
scraper/http/
-------------
HTTP istemci katmanı.

Dışa aktarılanlar:
  BaseHttpClient    → Soyut arayüz (bağımlılık tersine çevirme için)
  PlaywrightClient  → Gerçek Playwright implementasyonu
"""

from scraper.http.base import BaseHttpClient
from scraper.http.playwright_client import PlaywrightClient

__all__ = ["BaseHttpClient", "PlaywrightClient"]