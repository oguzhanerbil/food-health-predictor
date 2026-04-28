"""
scraper/http/base.py
--------------------
Tüm HTTP istemcilerinin uyması gereken soyut arayüz.
Bağımlılık Tersine Çevirme: Orkestratör bu arayüze bağlıdır,
somut implementasyona değil.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseHttpClient(ABC):
    """HTTP istemcisi için soyut temel sınıf."""

    @abstractmethod
    def get(self, url: str, wait_for: Optional[str] = None) -> Optional[str]:
        """
        Belirtilen URL'yi getirir ve sayfa HTML'sini döndürür.
        Hata durumunda None döner.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """İstemci kaynaklarını serbest bırakır."""
        ...