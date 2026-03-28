"""
main.py
-------
Giriş noktası. Tüm bileşenleri bağlar ve taramayı başlatır.

Kullanım:
    python main.py                        # varsayılan yapılandırma ile çalıştır
    python main.py --pages 10            # 10 liste sayfası ile sınırlı
    python main.py --url "https://..."   # özel başlangıç URL'si
    python main.py --no-resume           # sıfırdan başla
"""

import argparse
import logging
import os
from pathlib import Path

from dotenv import load_dotenv


from config import ScraperConfig, DEFAULT_CONFIG
from scraper.playwright_client import PlaywrightClient
from scraper.listing_parser import ListingParser
from scraper.product_parser import ProductParser
from scraper.orchestrator import ScraperOrchestrator
from storage.csv_storage import CsvStorage
from utils.logging_config import configure_logging

logger = logging.getLogger(__name__)


# .env dosyasını yükle
def load_env():
    env_file = Path(__file__).parent / "auth.env"
    if env_file.exists():
        load_dotenv(env_file)
        logger.debug("✓ auth.env dosyası yüklendi")
    else:
        logger.debug("auth.env dosyası bulunamadı")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Nutri-Score verileri için OpenFoodFacts tarayıcısı.")
    parser.add_argument("--url", default=None, help="Başlangıç URL'sini geçersiz kıl.")
    parser.add_argument("--pages", type=int, default=None, help="Taranacak maksimum liste sayfaları.")
    parser.add_argument("--output", default=None, help="Çıktı CSV yolu.")
    parser.add_argument("--no-resume", action="store_true", help="Kaydedilen ilerlemeyi yok say.")
    parser.add_argument("--email", default=None, help="OpenFoodFacts email (10+ sayfa için)")
    parser.add_argument("--password", default=None, help="OpenFoodFacts şifre")
    parser.add_argument("--log-level", default="INFO", help="Günlük seviyesi.")
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> ScraperConfig:
    cfg = ScraperConfig(
        start_url=args.url or DEFAULT_CONFIG.start_url,
        max_pages=args.pages or DEFAULT_CONFIG.max_pages,
        output_csv=args.output or DEFAULT_CONFIG.output_csv,
        log_level=args.log_level,
        resume=not args.no_resume,
        off_email=args.email or os.getenv("OFF_EMAIL"),
        off_password=args.password or os.getenv("OFF_PASSWORD"),
    )
    return cfg


def main() -> None:
    # .env dosyasını yükle
    load_env()
    
    args = parse_args()
    cfg = build_config(args)

    configure_logging(log_level=cfg.log_level, log_file=cfg.log_file)
    logger.info("=== Nutri-Score Verileri için OpenFoodFacts Tarayıcısı Başlıyor ===")
    logger.info("Başlangıç URL'si : %s", cfg.start_url)
    logger.info("Maksimum sayfalar : %s", cfg.max_pages or "sınırsız")
    logger.info("Çıktı          : %s", cfg.output_csv)
    logger.info("Devam et      : %s", cfg.resume)

    # HTTP istemcisi, parser'lar ve orkestratör oluşturuluyor
    http_client = PlaywrightClient(
        min_delay=cfg.min_delay_seconds,
        max_delay=cfg.max_delay_seconds,
        retries=cfg.max_retries,
        timeout=cfg.request_timeout,
        email=cfg.off_email,
        password=cfg.off_password,
    )
    listing_parser = ListingParser()
    product_parser = ProductParser()
    orchestrator = ScraperOrchestrator(
        http_client=http_client,
        listing_parser=listing_parser,
        product_parser=product_parser,
        max_pages=cfg.max_pages,
    )

    saved_count = 0
    skipped_count = 0

    try:
        with CsvStorage(cfg.output_csv) as storage:
            # Resume support: load already-scraped URLs
            already_saved = storage.get_saved_urls() if cfg.resume else set()
            if already_saved:
                logger.info("Devam modu: CSV'de zaten %d URL var, bunlar atlanacak.", len(already_saved))

            for product in orchestrator.scrape(cfg.start_url):
                if product.url in already_saved:
                    skipped_count += 1
                    continue

                storage.save(product)
                saved_count += 1

                if saved_count % 50 == 0:
                    logger.info("İlerleme: %d kaydedildi, %d atlandı.", saved_count, skipped_count)

        logger.info("=== Tarama Tamamlandı ===")
        logger.info("Toplam kaydedilen  : %d", saved_count)
        logger.info("Toplam atlanan    : %d", skipped_count)
    except KeyboardInterrupt:
        logger.warning("Tarama kullanıcı tarafından durduruldu (Ctrl+C)")
        logger.info("Son durum - Kaydedilen: %d, Atlanan: %d", saved_count, skipped_count)


if __name__ == "__main__":
    main()