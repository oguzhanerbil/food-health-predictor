import requests
import pandas as pd
import os

FOLDER = "data"
os.makedirs(FOLDER, exist_ok=True)


def get_products_by_grade(grade, page=1):
    url = f"https://world.openfoodfacts.org/cgi/search.pl"

    params = {
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 50,
        "page": page,
        "nutrition_grades_tags": grade
    }

    r = requests.get(url, params=params)

    if r.status_code != 200:
        return []

    return r.json().get("products", [])


def parse_product(p):
    nutriments = p.get("nutriments", {})

    def f(x):
        try:
            return float(x)
        except:
            return None

    return {
        "energy_kcal": f(nutriments.get("energy-kcal_100g")),
        "fat_g": f(nutriments.get("fat_100g")),
        "carbohydrates_g": f(nutriments.get("carbohydrates_100g")),
        "sugars_g": f(nutriments.get("sugars_100g")),
        "proteins_g": f(nutriments.get("proteins_100g")),
        "salt_g": f(nutriments.get("salt_100g")),
        "nutriscore_grade": p.get("nutrition_grades")
    }


def scrape_grade(grade):
    data = []

    for page in range(1, 3):  # test: 2 sayfa
        print(f"{grade.upper()} - sayfa {page}")

        products = get_products_by_grade(grade, page)

        if not products:
            break

        for p in products:
            item = parse_product(p)

            # boşları at
            if any(v is not None for v in item.values()):
                data.append(item)

    if not data:
        print(f"❌ {grade} veri yok")
        return

    df = pd.DataFrame(data)
    path = f"{FOLDER}/{grade}_grade.csv"
    df.to_csv(path, index=False)

    print(f"✅ {path} kaydedildi ({len(data)})")


if __name__ == "__main__":
    for g in ["a", "b", "c", "d", "e"]:
        scrape_grade(g)