import pandas as pd

# A, B, C, D, E CSV dosyalarını oku
grade_files = ['grade_a.csv', 'grade_b.csv', 'grade_c.csv', 'grade_d.csv', 'grade_e.csv']

dataframes = []

for file in grade_files:
    try:
        df = pd.read_csv("data/"+file)
        dataframes.append(df)
        print(f"✓ {file} yüklendi ({len(df)} satır)")
    except FileNotFoundError:
        print(f"✗ {file} bulunamadı")

# Tüm dataframe'leri birleştir
if dataframes:
    combined_df = pd.concat(dataframes, ignore_index=True)
    print(f"\n{'='*50}")
    print(f"Toplam satır sayısı: {len(combined_df)}")
    print(f"Toplam sütun sayısı: {len(combined_df.columns)}")
    print(f"{'='*50}\n")
    
    # Birleştirilmiş veriyi ham_veri.csv olarak kaydet
    combined_df.to_csv('data/ham_data.csv', index=False, encoding='utf-8')
    print(f"✓ Birleştirilmiş veri 'ham_veri.csv' dosyasına kaydedildi")
else:
    print("Hiçbir CSV dosyası bulunamadı!")
