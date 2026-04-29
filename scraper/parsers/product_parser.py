"""
scraper/parsers/product_parser.py
-----------------------------------
Tek bir ürün detay sayfasını Product domain nesnesine dönüştürür.
Tek Sorumluluk: HTML → Product koordinasyonu.

Karmaşık alt görevler ayrı sınıflara devredilmiştir:
  NutritionTableParser  → Beslenme tablosu ayrıştırma + sütun tespiti
  NutrientMapper        → Besin etiketi → alan eşlemesi

v3 değişiklikleri (orijinalden korunmuştur):
  - Nutrition tablosunda dinamik sütun tespiti
  - Genişletilmiş besin desteği: monounsaturated/polyunsaturated fat,
    omega 3/6/9, starch, vitamin K, caffeine, cocoa, choline
  - Green-Score: src + h4 text çift strateji
  - NS component points: img src'den parse (JS'den bağımsız, robust)
"""

import re
import logging
from typing import Optional

from bs4 import BeautifulSoup

from models.product import Product, NutritionFacts, NutriScoreDetails
from .nutrition_table_parser import NutritionTableParser

logger = logging.getLogger(__name__)


class ProductParser:
    """Ürün detay sayfasını parse eder ve Product nesnesi döndürür."""

    def __init__(self) -> None:
        self._nutrition_table_parser = NutritionTableParser()

    def parse(self, html: str, url: str) -> Product:
        soup = BeautifulSoup(html, "lxml")
        product = Product(url=url)

        product.barcode  = self._text(soup, "#barcode")
        product.name     = (
            self._text(soup, "h2.title-1")
            or self._text(soup, "h1.title-1")
        )
        product.quantity             = self._field_value(soup, "field_quantity")
        product.packaging            = self._field_value(soup, "field_packaging")
        product.brands               = self._field_value(soup, "field_brands")
        product.categories           = self._field_value(soup, "field_categories")
        product.labels               = self._field_value(soup, "field_labels")
        product.origins              = (
            self._field_value(soup, "field_origin")
            or self._field_value(soup, "field_origins")
        )
        product.manufacturing_places = self._field_value(soup, "field_manufacturing_places")
        product.countries_sold       = self._field_value(soup, "field_countries")

        self._parse_scores(soup, product)
        self._parse_ingredients(soup, product)
        self._parse_nutrient_levels(soup, product)
        self._nutrition_table_parser.parse(soup, product.nutrition)
        self._parse_nutriscore_details(soup, product)
        self._parse_ingredient_analysis(soup, product)

        return product

    # ------------------------------------------------------------------ #
    # Skor rozetleri
    # ------------------------------------------------------------------ #

    def _parse_scores(self, soup: BeautifulSoup, product: Product) -> None:
        self._parse_nutriscore_grade(soup, product)
        self._parse_nova_group(soup, product)
        self._parse_green_score(soup, product)

    def _parse_nutriscore_grade(self, soup: BeautifulSoup, product: Product) -> None:
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

    def _parse_nova_group(self, soup: BeautifulSoup, product: Product) -> None:
        for img in soup.find_all("img", src=re.compile(r"nova-group-(\d)", re.I)):
            m = re.search(r"nova-group-(\d)", img.get("src", ""), re.I)
            if m:
                product.nova_group = int(m.group(1))
                break

    def _parse_green_score(self, soup: BeautifulSoup, product: Product) -> None:
        # Strateji 1: src içinde "green-score-b.svg" gibi grade var
        for img in soup.find_all("img", src=re.compile(r"green-score-[a-e]", re.I)):
            m = re.search(r"green-score-([a-e])", img.get("src", ""), re.I)
            if m:
                product.green_score_grade = m.group(1).upper()
                return

        # Strateji 2 (yedek): h4 içinde "Green-Score E" gibi metin
        for h4 in soup.find_all("h4"):
            m = re.search(r"Green-Score\s+([A-E])\b", h4.get_text(), re.I)
            if m:
                product.green_score_grade = m.group(1).upper()
                return

    # ------------------------------------------------------------------ #
    # İçerik listesi
    # ------------------------------------------------------------------ #

    def _parse_ingredients(self, soup: BeautifulSoup, product: Product) -> None:
        ing_panel = soup.find(id="panel_ingredients_content")
        if not ing_panel:
            return

        self._parse_ingredient_count(soup, product)
        self._parse_ingredient_text_and_allergens(ing_panel, product)

    def _parse_ingredient_count(self, soup: BeautifulSoup, product: Product) -> None:
        title_el = soup.find(id="panel_ingredients")
        if not title_el:
            return
        h4 = title_el.find("h4")
        if h4:
            m = re.search(r"(\d+)\s+ingredient", h4.get_text(), re.I)
            if m:
                product.ingredients_count = int(m.group(1))

    def _parse_ingredient_text_and_allergens(self, ing_panel, product: Product) -> None:
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
    # Nutri-Score ayrıntılı hesaplama
    # ------------------------------------------------------------------ #

    def _parse_nutriscore_details(self, soup: BeautifulSoup, product: Product) -> None:
        ns = product.nutriscore_details

        self._parse_nutriscore_points_from_h3(soup, ns)
        self._parse_nutriscore_score_from_panel(soup, ns, product)
        self._parse_nutriscore_component_points(soup, ns)

    def _parse_nutriscore_points_from_h3(self, soup: BeautifulSoup, ns: NutriScoreDetails) -> None:
        for h3 in soup.find_all("h3"):
            txt = h3.get_text(strip=True)
            m = re.search(r"Negative points:\s*(-?\d+)", txt)
            if m:
                ns.negative_points = int(m.group(1))
            m = re.search(r"Positive points:\s*(\d+)", txt)
            if m:
                ns.positive_points = int(m.group(1))

    def _parse_nutriscore_score_from_panel(
        self, soup: BeautifulSoup, ns: NutriScoreDetails, product: Product
    ) -> None:
        details_panel = soup.find(id="panel_nutriscore_details_content")
        if not details_panel:
            return
        txt = details_panel.get_text()
        m = re.search(r"Nutritional score:\s*(-?\d+)", txt)
        if m:
            ns.score = int(m.group(1))
        m = re.search(r"Nutri-Score:\s*([A-E])", txt, re.I)
        if m:
            ns.grade = m.group(1).upper()
            if not product.nutriscore_grade:
                product.nutriscore_grade = ns.grade

    def _parse_nutriscore_component_points(
        self, soup: BeautifulSoup, ns: NutriScoreDetails
    ) -> None:
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

            points = self._extract_component_points(panel)
            if points is not None:
                setattr(ns, attr, points)

    def _extract_component_points(self, panel) -> Optional[int]:
        """Bir bileşen panelinden puan değerini çıkarır."""
        # Birincil: img src "points-negative-1-10.svg" → 1
        img = panel.find("img", src=re.compile(r"points-(?:negative|positive)-", re.I))
        if img:
            m = re.search(
                r"points-(?:negative|positive)-(-?\d+)-\d+",
                img.get("src", ""), re.I,
            )
            if m:
                return int(m.group(1))

        # Yedek: span "X/Y points"
        for span in panel.find_all("span"):
            m = re.search(r"(-?\d+)/\d+\s+points", span.get_text())
            if m:
                return int(m.group(1))

        return None

    # ------------------------------------------------------------------ #
    # İçerik analizi
    # ------------------------------------------------------------------ #

    def _parse_ingredient_analysis(self, soup: BeautifulSoup, product: Product) -> None:
        """
        İçerik analizi panelini parse eder.
        Palm oil ve vegetarian için üç durum: True / False / None (belirsiz)
        """
        analysis_panel = soup.find(id="panel_ingredients_analysis_content")
        if not analysis_panel:
            return

        for li_panel in analysis_panel.find_all("li", class_="accordion-navigation"):
            h4 = li_panel.find("h4")
            if not h4:
                continue
            label = h4.get_text(strip=True).lower()
            self._apply_analysis_label(label, product)

    def _apply_analysis_label(self, label: str, product: Product) -> None:
        # Palm oil
        if "palm oil free" in label:
            product.is_palm_oil_free = True
        elif "may contain palm oil" in label or "might contain palm oil" in label:
            product.is_palm_oil_free = None
        elif "contains palm oil" in label or (
            "palm oil" in label and "free" not in label and "may" not in label
        ):
            product.is_palm_oil_free = False

        # Vegetarian
        if "non-vegetarian" in label or "not vegetarian" in label:
            product.is_vegetarian = False
        elif "maybe vegetarian" in label:
            product.is_vegetarian = None
        elif "vegetarian" in label and "maybe" not in label:
            product.is_vegetarian = True

        # Vegan
        if "vegan" in label and "vegetarian" not in label:
            if "maybe" in label:
                product.is_vegan_status = "maybe"
            elif "non-vegan" in label or "not vegan" in label:
                product.is_vegan_status = "no"
            else:
                product.is_vegan_status = "yes"

    # ------------------------------------------------------------------ #
    # Statik yardımcılar
    # ------------------------------------------------------------------ #

    @staticmethod
    def _text(soup: BeautifulSoup, selector: str) -> Optional[str]:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else None

    @staticmethod
    def _field_value(soup: BeautifulSoup, field_id: str) -> Optional[str]:
        el = soup.find(id=f"{field_id}_value") or soup.find(id=field_id)
        return el.get_text(separator=", ", strip=True) if el else None