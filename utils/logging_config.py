"""
logging_config.py
-----------------
Günlük yapılandırması ve kurulumu.
"""

import logging
import logging.handlers
import os
from typing import Optional


def configure_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
) -> None:
    """
    Günlüğü yapılandırır: konsol ve dosya çıkışı.

    Args:
        log_level: Günlük seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Günlüklerin kaydedileceği dosya yolu. None ise sadece konsola yazılır.
        log_format: Özel günlük formatı. None ise varsayılan format kullanılır.
    """
    if log_format is None:
        log_format = (
            "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
        )

    # Root logger'ı yapılandır
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Konsol handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Dosya handler (eğer belirtilmişse)
    if log_file:
        # Dosya dizinini oluştur (eğer yoksa)
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,  # 5 yedek dosya tut
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
