"""
models/product.py
-----------------
Domain models for scraped product data.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NutritionFacts:
    energy_kj: Optional[float] = None
    energy_kcal: Optional[float] = None
    fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    sugars_g: Optional[float] = None
    fiber_g: Optional[float] = None
    proteins_g: Optional[float] = None
    salt_g: Optional[float] = None
    sodium_g: Optional[float] = None
    alcohol_pct: Optional[float] = None
    fruits_veg_legumes_pct: Optional[float] = None


@dataclass
class NutriScoreDetails:
    score: Optional[int] = None
    grade: Optional[str] = None          # A/B/C/D/E
    negative_points: Optional[int] = None
    positive_points: Optional[int] = None
    energy_points: Optional[int] = None
    sugars_points: Optional[int] = None
    saturated_fat_points: Optional[int] = None
    salt_points: Optional[int] = None
    proteins_points: Optional[int] = None
    fiber_points: Optional[int] = None
    fvl_points: Optional[int] = None     # fruits/veg/legumes


@dataclass
class Product:
    url: str
    barcode: Optional[str] = None
    name: Optional[str] = None
    quantity: Optional[str] = None
    packaging: Optional[str] = None
    brands: Optional[str] = None
    categories: Optional[str] = None
    labels: Optional[str] = None
    origins: Optional[str] = None
    manufacturing_places: Optional[str] = None
    countries_sold: Optional[str] = None

    # Ingredients
    ingredients_text: Optional[str] = None
    allergens: Optional[str] = None
    traces: Optional[str] = None
    ingredients_count: Optional[int] = None

    # Scores
    nutriscore_grade: Optional[str] = None
    nova_group: Optional[int] = None
    green_score_grade: Optional[str] = None

    # Ingredient analysis flags
    is_palm_oil_free: Optional[bool] = None
    is_vegetarian: Optional[bool] = None
    is_vegan_status: Optional[str] = None  # yes / maybe / no

    # Fat nutrient level
    fat_level: Optional[str] = None           # low / moderate / high
    saturated_fat_level: Optional[str] = None
    sugars_level: Optional[str] = None
    salt_level: Optional[str] = None

    # Nested objects
    nutrition: NutritionFacts = field(default_factory=NutritionFacts)
    nutriscore_details: NutriScoreDetails = field(default_factory=NutriScoreDetails)

    def to_flat_dict(self) -> dict:
        """Flatten to a single-level dict suitable for a DataFrame row."""
        d = {
            "url": self.url,
            "barkod": self.barcode,
            "urun_adi": self.name,
            "miktar": self.quantity,
            "ambalaj": self.packaging,
            "markalar": self.brands,
            "kategoriler": self.categories,
            "etiketler": self.labels,
            "mensei": self.origins,
            "uretim_yerleri": self.manufacturing_places,
            "satildigi_ulkeler": self.countries_sold,

            "icerik_metni": self.ingredients_text,
            "alerjenler": self.allergens,
            "eser_miktarlar": self.traces,
            "icerik_sayisi": self.ingredients_count,

            "nutriscore_notu": self.nutriscore_grade,
            "nova_grubu": self.nova_group,
            "yesil_skor_notu": self.green_score_grade,

            "palmiye_yagi_icermez": self.is_palm_oil_free,
            "vejetaryen": self.is_vegetarian,
            "vegan_durumu": self.is_vegan_status,

            "yag_seviyesi": self.fat_level,
            "doymus_yag_seviyesi": self.saturated_fat_level,
            "seker_seviyesi": self.sugars_level,
            "tuz_seviyesi": self.salt_level,

            # Nutrition facts
            "enerji_kj": self.nutrition.energy_kj,
            "enerji_kcal": self.nutrition.energy_kcal,
            "yag_g": self.nutrition.fat_g,
            "doymus_yag_g": self.nutrition.saturated_fat_g,
            "karbonhidrat_g": self.nutrition.carbohydrates_g,
            "seker_g": self.nutrition.sugars_g,
            "lif_g": self.nutrition.fiber_g,
            "protein_g": self.nutrition.proteins_g,
            "tuz_g": self.nutrition.salt_g,
            "sodyum_g": self.nutrition.sodium_g,
            "alkol_yuzde": self.nutrition.alcohol_pct,
            "meyve_sebze_baklagil_yuzde": self.nutrition.fruits_veg_legumes_pct,

            # NutriScore details
            "nutriscore_puan": self.nutriscore_details.score,
            "ns_negatif_puan": self.nutriscore_details.negative_points,
            "ns_pozitif_puan": self.nutriscore_details.positive_points,
            "ns_enerji_puan": self.nutriscore_details.energy_points,
            "ns_seker_puan": self.nutriscore_details.sugars_points,
            "ns_doymus_yag_puan": self.nutriscore_details.saturated_fat_points,
            "ns_tuz_puan": self.nutriscore_details.salt_points,
            "ns_protein_puan": self.nutriscore_details.proteins_points,
            "ns_lif_puan": self.nutriscore_details.fiber_points,
            "ns_meyve_sebze_baklagil_puan": self.nutriscore_details.fvl_points,
        }
        return d