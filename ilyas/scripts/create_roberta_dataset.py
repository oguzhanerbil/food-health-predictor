import pandas as pd

# Veri oku
df = pd.read_csv("ilyas/data/temiz_veri.csv")

# Boşları doldur
df = df.fillna("")

# Boş NutriScore kayıtlarını sil
df = df[df["nutriscore_notu"].notna()].copy()

# NutriScore sızıntılarını temizle
def temizle_etiketler(text):
    text = str(text)

    silinecekler = [
        "Nutriscore",
        "Nutriscore Grade A",
        "Nutriscore Grade B",
        "Nutriscore Grade C",
        "Nutriscore Grade D",
        "Nutriscore Grade E",
        "nutriscore-grade-a",
        "nutriscore-grade-b",
        "nutriscore-grade-c",
        "nutriscore-grade-d",
        "nutriscore-grade-e"
    ]

    for item in silinecekler:
        text = text.replace(item, "")

    return text.strip()

df["etiketler"] = df["etiketler"].apply(temizle_etiketler)

def create_text(row):

    return f"""
Ürün adı: {row['urun_adi']}

Marka: {row['markalar']}

Miktar: {row['miktar']}

Ürün kategorileri:
{row['kategoriler']}

Etiketler:
{row['etiketler']}

Alerjenler:
{row['alerjenler']}

İçindekiler:
{row['icerik_metni']}

İçerik sayısı:
{row['icerik_sayisi']}

Enerji: {row['enerji_kcal']} kcal
Yağ: {row['yag_g']} g
Doymuş yağ: {row['doymus_yag_g']} g
Karbonhidrat: {row['karbonhidrat_g']} g
Şeker: {row['seker_g']} g
Lif: {row['lif_g']} g
Protein: {row['protein_g']} g
Tuz: {row['tuz_g']} g

Nova grubu:
{row['nova_grubu']}

Yağ seviyesi:
{row['yag_seviyesi']}

Doymuş yağ seviyesi:
{row['doymus_yag_seviyesi']}

Şeker seviyesi:
{row['seker_seviyesi']}

Tuz seviyesi:
{row['tuz_seviyesi']}

Vejetaryen:
{row['vejetaryen']}

Vegan:
{row['vegan_durumu']}

Palmiye yağı içermez:
{row['palmiye_yagi_icermez']}
""".strip()

df["text"] = df.apply(create_text, axis=1)

roberta_df = df[["text", "nutriscore_notu"]].copy()
roberta_df.columns = ["text", "label"]

# Çok kısa kayıtları temizle
roberta_df = roberta_df[
    roberta_df["text"].str.len() > 50
]

roberta_df.to_csv(
    "ilyas/data/roberta_data.csv",
    index=False,
    encoding="utf-8-sig"
)

print("RoBERTa veri seti oluşturuldu.")
print("Veri boyutu:", roberta_df.shape)
print(roberta_df["label"].value_counts())