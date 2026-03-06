"""
config.py
---------
Tüm yapılandırma sabitleri tek bir yerde.
Tüm yapılandırma sabitleri tek bir yerde. İş mantığına dokunmadan buradaki değerleri değiştirebilirsiniz.
"""

from dataclasses import dataclass


@dataclass
class ScraperConfig:
    # Örneğin, sadece "A" Nutri-Score'lu ürünleri taramak için:
    start_url: str = "https://world.openfoodfacts.org/facets/nutrition-grades/a"

    # None = her şeyi tarar; test için 5 gibi bir tamsayı belirleyin
    max_pages: int | None = None

    # HTTP
    min_delay_seconds: float = 1.5
    max_delay_seconds: float = 5.5
    request_timeout: int = 60
    max_retries: int = 3

    # Çıktı ve günlük
    output_csv: str = "data/products.csv"
    log_file: str = "logs/scraper.log"
    log_level: str = "INFO"

    # Devam et: zaten taranmış URL'leri atla
    resume: bool = True


# Varsayılan örnek — bunu main.py'de içe aktarın
DEFAULT_CONFIG = ScraperConfig()