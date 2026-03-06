"""
scraper/product_parser.py
-------------------------
Parses a single product detail page into a Product domain object.
Single Responsibility: HTML → Product only.

v3 değişiklikleri:
  - Nutrition tablosunda dinamik sütun tespiti:
    Önce "As sold for 100 g / 100 ml" sütununu bulur, sonraki sütunlarla
    karıştırmadan sadece o sütunu okur.
  - Genişletilmiş besin desteği: monounsaturated/polyunsaturated fat,
    omega 3/6/9, starch, vitamin K, caffeine, cocoa, choline
  - Green-Score: src + h4 text çift strateji (alt="Green-Score icon" grade içermiyor)
  - NS component points: img src'den parse (JS'den bağımsız, robust)
"""

import re
import logging
from typing import Optional
from bs4 import BeautifulSoup

from models.product import Product, NutritionFacts, NutriScoreDetails

logger = logging.getLogger(__name__)


class ProductParser:

    def parse(self, html: str, url: str) -> Product:
        soup = BeautifulSoup(html, "lxml")
        product = Product(url=url)

        product.barcode       = self._text(soup, "#barcode")
        product.name          = (
            self._text(soup, "h2.title-1")
            or self._text(soup, "h1.title-1")
        )
        product.quantity      = self._field_value(soup, "field_quantity")
        product.packaging     = self._field_value(soup, "field_packaging")
        product.brands        = self._field_value(soup, "field_brands")
        product.categories    = self._field_value(soup, "field_categories")
        product.labels        = self._field_value(soup, "field_labels")
        product.origins       = (
            self._field_value(soup, "field_origin")
            or self._field_value(soup, "field_origins")
        )
        product.manufacturing_places = self._field_value(soup, "field_manufacturing_places")
        product.countries_sold       = self._field_value(soup, "field_countries")

        self._parse_scores(soup, product)
        self._parse_ingredients(soup, product)
        self._parse_nutrient_levels(soup, product)
        self._parse_nutrition_facts(soup, product)
        self._parse_nutriscore_details(soup, product)
        self._parse_ingredient_analysis(soup, product)

        return product

    # ------------------------------------------------------------------ #
    # Skor rozetleri
    # ------------------------------------------------------------------ #

    def _parse_scores(self, soup: BeautifulSoup, product: Product) -> None:
        # --- Nutri-Score ---
        for img in soup.find_all("img"):
            alt = img.get("alt", "")
            src = img.get("src", "")
            m = re.search(r"Nutri-Score\s+([A-E])\b", alt, re.I)
            if m:
                product.nutriscore_grade = m.group(1).upper()
                break
            m = re.search(r"nutriscore-([a-e])(?:-new)?(?:-en)?\.svg", src, re.I)
            if m:
                product.nutriscore_grade = m.group(1).upper()
                break

        # --- NOVA grubu ---
        for img in soup.find_all("img", src=re.compile(r"nova-group-(\d)", re.I)):
            m = re.search(r"nova-group-(\d)", img.get("src", ""), re.I)
            if m:
                product.nova_group = int(m.group(1))
                break

        # --- Green-Score ---
        # Strateji 1: src içinde "green-score-b.svg" gibi grade var
        # (alt="Green-Score icon" — grade içermiyor, bu yüzden src öncelikli)
        for img in soup.find_all("img", src=re.compile(r"green-score-[a-e]", re.I)):
            m = re.search(r"green-score-([a-e])", img.get("src", ""), re.I)
            if m:
                product.green_score_grade = m.group(1).upper()
                break

        # Strateji 2 (yedek): h4 içinde "Green-Score E" gibi metin
        if not product.green_score_grade:
            for h4 in soup.find_all("h4"):
                m = re.search(r"Green-Score\s+([A-E])\b", h4.get_text(), re.I)
                if m:
                    product.green_score_grade = m.group(1).upper()
                    break

    # ------------------------------------------------------------------ #
    # İçerik listesi
    # ------------------------------------------------------------------ #

    def _parse_ingredients(self, soup: BeautifulSoup, product: Product) -> None:
        ing_panel = soup.find(id="panel_ingredients_content")
        if not ing_panel:
            return

        title_el = soup.find(id="panel_ingredients")
        if title_el:
            h4 = title_el.find("h4")
            if h4:
                m = re.search(r"(\d+)\s+ingredient", h4.get_text(), re.I)
                if m:
                    product.ingredients_count = int(m.group(1))

        text_div = ing_panel.find("div", class_="panel_text")
        if text_div:
            product.ingredients_text = text_div.get_text(separator=" ", strip=True)

        for block in ing_panel.find_all("div", class_="panel_text"):
            txt = block.get_text(strip=True)
            if txt.startswith("Allergens:"):
                product.allergens = txt.replace("Allergens:", "").strip()
            elif txt.startswith("Traces:"):
                product.traces = txt.replace("Traces:", "").strip()

    # ------------------------------------------------------------------ #
    # Besin maddesi seviyeleri (low / moderate / high)
    # ------------------------------------------------------------------ #

    def _parse_nutrient_levels(self, soup: BeautifulSoup, product: Product) -> None:
        level_map = {
            "panel_nutrient_level_fat":           "fat_level",
            "panel_nutrient_level_saturated-fat": "saturated_fat_level",
            "panel_nutrient_level_sugars":        "sugars_level",
            "panel_nutrient_level_salt":          "salt_level",
        }
        for panel_id, attr in level_map.items():
            panel = soup.find(id=panel_id)
            if not panel:
                continue
            h4 = panel.find("h4")
            txt = h4.get_text(strip=True).lower() if h4 else ""
            if not txt:
                img = panel.find("img")
                txt = img.get("src", "").lower() if img else ""
            if "low" in txt:
                setattr(product, attr, "low")
            elif "moderate" in txt:
                setattr(product, attr, "moderate")
            elif "high" in txt:
                setattr(product, attr, "high")

    # ------------------------------------------------------------------ #
    # Besin değerleri tablosu — dinamik sütun tespiti
    # ------------------------------------------------------------------ #

    def _parse_nutrition_facts(self, soup: BeautifulSoup, product: Product) -> None:
        """
        İki tablo kaynağını dener:
          1. panel_nutrition_facts_table_content          (standart)
          2. panel_nutrition_facts_table_with_input_sets_content (detaylı, çok sütunlu)

        Her iki tabloda da "As sold for 100 g / 100 ml" sütununu dinamik olarak
        tespit eder — sütun sayısına göre doğru indexi seçer.
        """
        panel_ids = [
            "panel_nutrition_facts_table_content",
            "panel_nutrition_facts_table_with_input_sets_content",
        ]
        for pid in panel_ids:
            panel = soup.find(id=pid)
            if not panel:
                continue
            table = panel.find("table")
            if not table:
                continue

            col_idx = self._find_per100g_column(table)
            self._extract_nutrition_rows(table, col_idx, product.nutrition)
            break  # ilk bulunan tabloyu kullan

    def _find_per100g_column(self, table) -> int:
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
            # "as sold for 100 g / 100 ml" — serving veya estimate DEĞİL
            if (
                "100 g" in txt
                and "100 ml" in txt
                and "serving" not in txt
                and "packaging" not in txt
                and "estimate" not in txt
            ):
                return i
        return 1  # varsayılan: ikinci sütun

    def _extract_nutrition_rows(
        self, table, col_idx: int, nf: NutritionFacts
    ) -> None:
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
            # Gereksiz whitespace ve unicode temizleme
            label = re.sub(r"\s+", " ", label).strip()
            value_text = cells[col_idx].get_text(" ", strip=True)

            self._map_nutrient(label, value_text, nf)

    def _map_nutrient(
        self, label: str, value_text: str, nf: NutritionFacts
    ) -> None:
        """
        Label → NutritionFacts alanı eşlemesi.

        Kural: En spesifik eşleşme her zaman önce gelir.
        "fat" içeren alt tipler (saturated, monounsaturated, ...)
        genel "fat" kontrolünden önce değerlendirilir — yanlış alana
        yazılma riski yoktur.
        """
        val = self._parse_nutrient_value(value_text)

        # ── Enerji ────────────────────────────────────────────────────────
        if "energy" in label:
            nf.energy_kj   = self._extract_number(value_text, "kj")
            nf.energy_kcal = self._extract_number(value_text, "kcal")

        # ── Yağlar — spesifikten genel'e ─────────────────────────────────
        # "saturated fat", "monounsaturated fat" gibi label'lar "fat" da
        # içerdiğinden genel "fat" kontrolü en sona bırakılır.
        elif "omega 3" in label or "omega-3" in label:
            nf.omega3_fat_g = val
        elif "omega 6" in label or "omega-6" in label:
            nf.omega6_fat_g = val
        elif "omega 9" in label or "omega-9" in label:
            nf.omega9_fat_g = val
        elif "monounsaturated" in label:         # "monounsaturated fat"
            nf.monounsaturated_fat_g = val
        elif "polyunsaturated" in label:         # "polyunsaturated fat"
            nf.polyunsaturated_fat_g = val
        elif "trans fat" in label or "trans-fat" in label:
            nf.trans_fat_g = val
        elif "saturated fat" in label:           # "saturated fat" — "fat" içeriyor ama önce yakalanır
            nf.saturated_fat_g = val
        elif label == "fat":                     # tam eşleşme — alt tipler buraya düşmez
            nf.fat_g = val

        # ── Karbonhidratlar — spesifikten genel'e ────────────────────────
        # "starch" ve "sugars" karbonhidrat alt tipleri — genel "carbohydrate"
        # kontrolünden önce gelir.
        elif "starch" in label:
            nf.starch_g = val
        elif "sugars" in label or label == "sugar":
            nf.sugars_g = val
        elif "carbohydrate" in label:            # "starch"/"sugars" buraya düşmez
            nf.carbohydrates_g = val

        # ── Diğer makro ──────────────────────────────────────────────────
        elif "fiber" in label or "fibre" in label:
            nf.fiber_g = val
        elif "protein" in label:
            nf.proteins_g = val

        # ── Tuz / mineraller ─────────────────────────────────────────────
        # "sodium" label'ı "salt" içermez; "salt" label'ı "sodium" içermez.
        # Yine de tam eşleşme kullanılır — gelecekteki "potassium salt" gibi
        # label'ların yanlış alana yazılması önlenir.
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
    # Nutri-Score ayrıntılı hesaplama
    # ------------------------------------------------------------------ #

    def _parse_nutriscore_details(self, soup: BeautifulSoup, product: Product) -> None:
        ns = product.nutriscore_details

        for h3 in soup.find_all("h3"):
            txt = h3.get_text(strip=True)
            m = re.search(r"Negative points:\s*(-?\d+)", txt)
            if m:
                ns.negative_points = int(m.group(1))
            m = re.search(r"Positive points:\s*(\d+)", txt)
            if m:
                ns.positive_points = int(m.group(1))

        details_panel = soup.find(id="panel_nutriscore_details_content")
        if details_panel:
            txt = details_panel.get_text()
            m = re.search(r"Nutritional score:\s*(-?\d+)", txt)
            if m:
                ns.score = int(m.group(1))
            m = re.search(r"Nutri-Score:\s*([A-E])", txt, re.I)
            if m:
                ns.grade = m.group(1).upper()
                if not product.nutriscore_grade:
                    product.nutriscore_grade = ns.grade

        # Bileşen puanları — img src (en güvenilir, JS'den bağımsız)
        component_map = {
            "panel_nutriscore_component_energy":                    "energy_points",
            "panel_nutriscore_component_sugars":                    "sugars_points",
            "panel_nutriscore_component_saturated_fat":             "saturated_fat_points",
            "panel_nutriscore_component_salt":                      "salt_points",
            "panel_nutriscore_component_proteins":                  "proteins_points",
            "panel_nutriscore_component_fiber":                     "fiber_points",
            "panel_nutriscore_component_fruits_vegetables_legumes": "fvl_points",
        }
        for panel_id, attr in component_map.items():
            panel = soup.find(id=panel_id)
            if not panel:
                continue

            points = None
            # Birincil: img src "points-negative-1-10.svg" → 1
            img = panel.find(
                "img", src=re.compile(r"points-(?:negative|positive)-", re.I)
            )
            if img:
                m = re.search(
                    r"points-(?:negative|positive)-(-?\d+)-\d+",
                    img.get("src", ""), re.I,
                )
                if m:
                    points = int(m.group(1))

            # Yedek: span "X/Y points"
            if points is None:
                for span in panel.find_all("span"):
                    m = re.search(r"(-?\d+)/\d+\s+points", span.get_text())
                    if m:
                        points = int(m.group(1))
                        break

            if points is not None:
                setattr(ns, attr, points)

    # ------------------------------------------------------------------ #
    # İçerik analizi
    # ------------------------------------------------------------------ #

    def _parse_ingredient_analysis(self, soup: BeautifulSoup, product: Product) -> None:
        """
        İçerik analizi panelini parse eder.
        Palm oil ve vegetarian için üç durum: True / False / None(maybe)

        is_palm_oil_free:
          True  <- "palm oil free"
          False <- "contains palm oil"
          None  <- "may contain palm oil" (belirsiz)

        is_vegetarian:
          True  <- "vegetarian" (kesin)
          False <- "non-vegetarian"
          None  <- "maybe vegetarian" (belirsiz)
        """
        analysis_panel = soup.find(id="panel_ingredients_analysis_content")
        if not analysis_panel:
            return

        for li_panel in analysis_panel.find_all("li", class_="accordion-navigation"):
            h4 = li_panel.find("h4")
            if not h4:
                continue
            label = h4.get_text(strip=True).lower()

            # Palm oil
            if "palm oil free" in label:
                product.is_palm_oil_free = True
            elif "may contain palm oil" in label or "might contain palm oil" in label:
                product.is_palm_oil_free = None   # belirsiz
            elif "contains palm oil" in label or (
                "palm oil" in label and "free" not in label and "may" not in label
            ):
                product.is_palm_oil_free = False

            # Vegetarian
            if "non-vegetarian" in label or "not vegetarian" in label:
                product.is_vegetarian = False
            elif "maybe vegetarian" in label:
                product.is_vegetarian = None       # belirsiz
            elif "vegetarian" in label and "maybe" not in label:
                product.is_vegetarian = True

            # Vegan (string: yes / maybe / no)
            if "vegan" in label and "vegetarian" not in label:
                if "maybe" in label:
                    product.is_vegan_status = "maybe"
                elif "non-vegan" in label or "not vegan" in label:
                    product.is_vegan_status = "no"
                else:
                    product.is_vegan_status = "yes"

    # ------------------------------------------------------------------ #
    # Yardımcı metodlar
    # ------------------------------------------------------------------ #

    @staticmethod
    def _text(soup: BeautifulSoup, selector: str) -> Optional[str]:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else None

    @staticmethod
    def _field_value(soup: BeautifulSoup, field_id: str) -> Optional[str]:
        el = soup.find(id=f"{field_id}_value") or soup.find(id=field_id)
        return el.get_text(separator=", ", strip=True) if el else None

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
    def _parse_float(text: str) -> Optional[float]:
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