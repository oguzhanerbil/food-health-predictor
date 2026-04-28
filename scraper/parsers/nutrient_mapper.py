"""
scraper/parsers/nutrient_mapper.py
------------------------------------
Besin etiketi → NutritionFacts alan eşleyicisi.
Tek Sorumluluk: ham etiket metni + ham değer metni → NutritionFacts nesnesine yazma.

ProductParser'dan ayrılma nedeni: eşleme mantığı bağımsız olarak test edilebilmeli
ve genişletilmesi gerektiğinde (yeni besin ekleme) tek bir yerde değişiklik yeterli olmalı.
"""

import re
import logging
from typing import Optional

from models.product import NutritionFacts

logger = logging.getLogger(__name__)


class NutrientMapper:
    """Ham besin satır verilerini NutritionFacts alanlarına eşler."""

    def map(self, label: str, value_text: str, nf: NutritionFacts) -> None:
        """
        Kural: En spesifik eşleşme her zaman önce gelir.
        "fat" içeren alt tipler (saturated, monounsaturated, ...)
        genel "fat" kontrolünden önce değerlendirilir.
        """
        val = self._parse_nutrient_value(value_text)

        # ── Enerji ────────────────────────────────────────────────────────
        if "energy" in label:
            nf.energy_kj   = self._extract_number(value_text, "kj")
            nf.energy_kcal = self._extract_number(value_text, "kcal")

        # ── Yağlar — spesifikten genel'e ─────────────────────────────────
        elif "omega 3" in label or "omega-3" in label:
            nf.omega3_fat_g = val
        elif "omega 6" in label or "omega-6" in label:
            nf.omega6_fat_g = val
        elif "omega 9" in label or "omega-9" in label:
            nf.omega9_fat_g = val
        elif "monounsaturated" in label:
            nf.monounsaturated_fat_g = val
        elif "polyunsaturated" in label:
            nf.polyunsaturated_fat_g = val
        elif "trans fat" in label or "trans-fat" in label:
            nf.trans_fat_g = val
        elif "saturated fat" in label:
            nf.saturated_fat_g = val
        elif label == "fat":
            nf.fat_g = val

        # ── Karbonhidratlar — spesifikten genel'e ────────────────────────
        elif "starch" in label:
            nf.starch_g = val
        elif "sugars" in label or label == "sugar":
            nf.sugars_g = val
        elif "carbohydrate" in label:
            nf.carbohydrates_g = val

        # ── Diğer makro ──────────────────────────────────────────────────
        elif "fiber" in label or "fibre" in label:
            nf.fiber_g = val
        elif "protein" in label:
            nf.proteins_g = val

        # ── Tuz / mineraller ─────────────────────────────────────────────
        elif label == "salt":
            nf.salt_g = val
        elif "sodium" in label:
            nf.sodium_g = val

        # ── Özel bileşenler ───────────────────────────────────────────────
        elif "alcohol" in label:
            nf.alcohol_pct = val
        elif "caffeine" in label:
            nf.caffeine_g = val
        elif "vitamin k" in label:
            nf.vitamin_k_g = val
        elif "cocoa" in label:
            nf.cocoa_pct = val
        elif "choline" in label:
            nf.choline_g = val
        elif "fruit" in label or "vegetable" in label or "legume" in label:
            nf.fruits_veg_legumes_pct = val
        else:
            logger.debug("Bilinmeyen besin etiketi atlandı: %r", label)

    # ------------------------------------------------------------------ #
    # Statik yardımcılar
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_nutrient_value(text: str) -> Optional[float]:
        """
        "55 g", "~ 2.5 g", "? g", "0 %" gibi değerleri parse eder.
        "?" veya boş ise None döner.
        """
        text = text.replace("~", "").strip()
        if not text or text.startswith("?"):
            return None
        m = re.search(r"[-+]?\d+[\.,]?\d*", text.replace(",", "."))
        if m:
            try:
                return float(m.group().replace(",", "."))
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_number(text: str, unit: str) -> Optional[float]:
        pattern = rf"([\d,\.]+)\s*{unit}"
        m = re.search(pattern, text, re.I)
        if m:
            try:
                return float(m.group(1).replace(",", "."))
            except ValueError:
                return None
        return None