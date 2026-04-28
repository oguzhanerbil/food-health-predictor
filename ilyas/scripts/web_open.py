import requests
import pandas as pd
import time
import os

# Verileri 'data' klasörüne atalım (scripts içindesin diye ../ ile çıkıyoruz)
FOLDER = "../data/"
os.makedirs(FOLDER, exist_ok=True)

def grade_verisi_cek(grade, sayfa_sayisi=3):
    url = "https://world.openfoodfacts.org/cgi/search.pl"
    all_products = []
    
    for page in range(1, sayfa_sayisi + 1):
        print(f"🔄 {grade.upper()} Grubu çekiliyor - Sayfa {page}")
        params = {
            "action": "process",
            "nutrition_grades_tags": grade,
            "json": 1,
            "page": page,
            "page_size": 50,
            # Tek seferde tüm kolonları istiyoruz
            "fields": "url,code,product_name,quantity,packaging,brands,categories,labels,origins,manufacturing_places,countries,ingredients_text,allergens,traces,ingredients_n,nutrition_grades,nova_group,ecoscore_grade,ingredients_analysis_tags,nutrient_levels,nutriments,nutriscore_score,nutriscore_data"
        }
        
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                products = r.json().get("products", [])
                if not products: break
                
                for p in products:
                    nut = p.get("nutriments", {})
                    # Senin istediğin kolonların API karşılıkları
                    item = {
                        "url": p.get("url"),
                        "barkod": p.get("code"),
                        "urun_adi": p.get("product_name"),
                        "nutriscore_notu": p.get("nutrition_grades"),
                        "enerji_kcal": nut.get("energy-kcal_100g"),
                        "seker_g": nut.get("sugars_100g"),
                        "protein_g": nut.get("proteins_100g"),
                        "yag_g": nut.get("fat_100g")
                        # Buraya istediğin diğer kolonları ekleyebilirsin reisim
                    }
                    all_products.append(item)
            time.sleep(1)
        except Exception as e:
            print(f"Hata: {e}")
            break
            
    if all_products:
        df = pd.DataFrame(all_products)
        df.to_csv(f"{FOLDER}{grade}_grade.csv", index=False, encoding="utf-8-sig")
        print(f"✅ {grade}_grade.csv kaydedildi.")