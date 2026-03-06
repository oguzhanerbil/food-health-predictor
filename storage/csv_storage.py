"""
storage/csv_storage.py
----------------------
Ürün nesnelerini satır satır CSV dosyasına kaydeder (akış yazma).
Sadece I/O, ayrıştırma mantığı yok.
StorageBase'i uygulayarak Parquet, DB vb. ile değiştirme.
"""

import csv
import logging
import os
from pathlib import Path
from typing import Set

from models.product import Product

logger = logging.getLogger(__name__)


class StorageBase:
    def save(self, product: Product) -> None:
        raise NotImplementedError

    def get_saved_urls(self) -> Set[str]:
        raise NotImplementedError


class CsvStorage(StorageBase):
    def __init__(self, output_path: str = "data/products.csv"):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._writer = None
        self._file = None
        self._fieldnames = None
        self._init_file()

    def _init_file(self) -> None:
        dummy = Product(url="dummy")
        self._fieldnames = list(dummy.to_flat_dict().keys())

        file_exists = self.output_path.exists() and self.output_path.stat().st_size > 0
        self._file = open(self.output_path, "a", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(
            self._file,
            fieldnames=self._fieldnames,
            extrasaction="ignore",
        )
        if not file_exists:
            self._writer.writeheader()
            self._file.flush()
            logger.info("Yeni CSV oluşturuldu: %s", self.output_path)
        else:
            logger.info("Var olan CSV'ye ekleniyor: %s", self.output_path)

    def save(self, product: Product) -> None:
        row = product.to_flat_dict()
        self._writer.writerow(row)
        self._file.flush()

    def get_saved_urls(self) -> Set[str]:
        """Devam desteği için zaten taranmış URL'lerin kümesini döndürür."""
        if not self.output_path.exists():
            return set()
        saved: Set[str] = set()
        try:
            with open(self.output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("url"):
                        saved.add(row["url"])
        except Exception as exc:
            logger.warning("Devam desteği için mevcut CSV okunamadı: %s", exc)
        return saved

    def close(self) -> None:
        if self._file:
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()