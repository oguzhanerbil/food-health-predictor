import pandas as pd

# Veriyi oku
df = pd.read_csv("ilyas/data/temiz_veri.csv")

# Kullanılacak sütunlar
columns = [
    "enerji_kcal",
    "yag_g",
    "doymus_yag_g",
    "karbonhidrat_g",
    "seker_g",
    "protein_g",
    "tuz_g",
    "lif_g",
    "sodyum_g",
    "nova_grubu",
    "nutriscore_notu"
]

# Gerekli sütunları al
df = df[columns]

print("İlk veri boyutu:", df.shape)

# Tekrar edenleri sil
df = df.drop_duplicates()

# Hedef kontrolü
valid_scores = ["A", "B", "C", "D", "E"]
df = df[df["nutriscore_notu"].isin(valid_scores)]

# Ana sütunlar boşsa sil
main_cols = [
    "enerji_kcal",
    "yag_g",
    "doymus_yag_g",
    "karbonhidrat_g",
    "seker_g",
    "protein_g",
    "tuz_g"
]

df = df.dropna(subset=main_cols)

# Yardımcı sütunları doldur
extra_cols = ["lif_g", "sodyum_g", "nova_grubu"]

for col in extra_cols:
    df[col] = df[col].fillna(df[col].median())

# Negatif değerleri sil
numeric_cols = columns[:-1]

for col in numeric_cols:
    df = df[df[col] >= 0]

# -------------------
# Feature Engineering
# -------------------

df["seker_orani"] = df["seker_g"] / (df["karbonhidrat_g"] + 1)
df["protein_orani"] = df["protein_g"] / (df["enerji_kcal"] + 1)
df["doymus_yag_orani"] = df["doymus_yag_g"] / (df["yag_g"] + 1)

print("Temiz veri boyutu:", df.shape)

# Kaydet
df.to_csv("ilyas/data/model_veri.csv", index=False, encoding="utf-8-sig")

print("Feature engineering tamamlandı. Model verisi hazır.")