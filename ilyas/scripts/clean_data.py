import pandas as pd

# Veriyi oku
df = pd.read_csv("ilyas/data/tüm_veri.csv")

print("İlk veri boyutu:", df.shape)

# Tamamen boş satırları sil
df = df.dropna(how="all")

# Tekrar eden satırları sil
df = df.drop_duplicates()

# Hedef sütunu boş olanları sil
df = df[df["nutriscore_notu"].notna()]

# Yazı sütunlarında boşluk temizliği
text_columns = df.select_dtypes(include=["object", "string"]).columns

for col in text_columns:
    df[col] = df[col].astype(str).str.strip()

# Sayısal sütunlar
numeric_columns = [
    "enerji_kcal",
    "yag_g",
    "doymus_yag_g",
    "karbonhidrat_g",
    "seker_g",
    "lif_g",
    "protein_g",
    "tuz_g",
    "sodyum_g"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Negatif değerleri NaN yap
for col in numeric_columns:
    df.loc[df[col] < 0, col] = pd.NA

print("Temizlenmiş veri boyutu:", df.shape)

# Kaydet
df.to_csv("ilyas/data/temiz_veri.csv", index=False, encoding="utf-8-sig")

print("Temizleme işlemi tamamlandı.")