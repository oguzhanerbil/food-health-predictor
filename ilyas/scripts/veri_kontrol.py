import pandas as pd

df = pd.read_csv("ilyas/data/temiz_veri.csv")

print("=" * 80)
print("SATIR / SÜTUN")
print("=" * 80)
print(df.shape)

print("\n" + "=" * 80)
print("SÜTUNLAR")
print("=" * 80)

for col in df.columns:
    print(col)

print("\n" + "=" * 80)
print("DOLULUK ORANLARI")
print("=" * 80)

for col in df.columns:

    bos = df[col].isna().sum()

    dolu = len(df) - bos

    oran = dolu / len(df) * 100

    print(
        f"{col:<35} "
        f"Dolu:{dolu:<8} "
        f"Boş:{bos:<8} "
        f"Doluluk:%{oran:.2f}"
    )

print("\n" + "=" * 80)
print("NUTRISCORE DAĞILIMI")
print("=" * 80)

print(df["nutriscore_notu"].value_counts(dropna=False))

incele = [
    "nova_grubu",
    "vegan_durumu",
    "vejetaryen",
    "palmiye_yagi_icermez",
    "yag_seviyesi",
    "doymus_yag_seviyesi",
    "seker_seviyesi",
    "tuz_seviyesi",
    "etiketler",
    "kategoriler"
]

for col in incele:

    if col in df.columns:

        print("\n" + "=" * 80)
        print(col.upper())
        print("=" * 80)

        try:
            print(
                df[col]
                .value_counts(dropna=False)
                .head(30)
            )
        except:
            pass

print("\n" + "=" * 80)
print("SAYISAL ALANLAR")
print("=" * 80)

sayisallar = [
    "enerji_kcal",
    "yag_g",
    "doymus_yag_g",
    "karbonhidrat_g",
    "seker_g",
    "lif_g",
    "protein_g",
    "tuz_g",
    "icerik_sayisi",
    "meyve_sebze_baklagil_yuzde",
    "alkol_yuzde"
]

for col in sayisallar:

    if col in df.columns:

        print("\n" + "=" * 80)
        print(col.upper())
        print("=" * 80)

        print(df[col].describe())

print("\nBİTTİ")


print("\nOUTLIER ANALIZI")

print("Tuz > 100:", (df["tuz_g"] > 100).sum())
print("Yağ > 100:", (df["yag_g"] > 100).sum())
print("Şeker > 100:", (df["seker_g"] > 100).sum())
print("Protein > 100:", (df["protein_g"] > 100).sum())
print("Enerji > 1000:", (df["enerji_kcal"] > 1000).sum())