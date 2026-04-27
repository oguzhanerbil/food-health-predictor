import pandas as pd

files = [
    "data/grade_a.csv",
    "data/grade_b.csv",
    "data/grade_c.csv",
    "data/grade_d.csv",
    "data/grade_e.csv"
]

dfs = []

for file in files:
    try:
        df = pd.read_csv(file)
        dfs.append(df)
        print(f"{file} okundu: {df.shape}")
    except Exception as e:
        print(f"HATA -> {file}: {e}")

if dfs:
    combined = pd.concat(dfs, ignore_index=True)

    print("Toplam veri:", combined.shape)

    combined.to_csv(
        "ilyas/data/tüm_veri.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("Birleştirme tamamlandı.")
else:
    print("Hiç veri okunamadı.")