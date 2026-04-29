"""
scraper/core/
-------------
Tarama sürecini koordine eden katman.

Dışa aktarılanlar:
  ScraperOrchestrator → Ana koordinatör; listeleme + ürün döngüsünü yönetir
"""

from scraper.core.orchestractor import ScraperOrchestrator

__all__ = ["ScraperOrchestrator"]