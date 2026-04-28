import requests


class Product:

    def __init__(self):
        self.energy_kcal = None
        self.fat_g = None
        self.carbohydrates_g = None
        self.sugars_g = None
        self.proteins_g = None
        self.salt_g = None
        self.nutriscore_grade = None

    def to_dict(self):
        return self.__dict__


class ProductParser:

    def parse(self, url):
        try:
            # 🔥 barcode çek
            barcode = url.split("/product/")[1].split("/")[0]

            # 🔥 YENİ API (EN ÖNEMLİ FIX)
            api_url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}"

            r = requests.get(api_url)

            if r.status_code != 200:
                return None

            data = r.json().get("product", {})
            nutriments = data.get("nutriments", {})

            def f(x):
                try:
                    return float(x)
                except:
                    return None

            p = Product()

            p.energy_kcal = f(nutriments.get("energy-kcal_100g"))
            p.fat_g = f(nutriments.get("fat_100g"))
            p.carbohydrates_g = f(nutriments.get("carbohydrates_100g"))
            p.sugars_g = f(nutriments.get("sugars_100g"))
            p.proteins_g = f(nutriments.get("proteins_100g"))
            p.salt_g = f(nutriments.get("salt_100g"))

            p.nutriscore_grade = data.get("nutriscore_grade")

            return p

        except Exception as e:
            print("❌ parser hata:", e)
            return None