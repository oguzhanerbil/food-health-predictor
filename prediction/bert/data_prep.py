import pandas as pd
from sklearn.model_selection import train_test_split
import os

def prepare_data():
    # Dosya yolları
    # Bu script prediction/bert klasöründen çalıştırılacağı için bağıl yol:
    input_path = '../../data/data.csv'
    output_dir = '.'
    
    print(f"{input_path} dosyası okunuyor...")
    df = pd.read_csv(input_path)
    
    # Hedef değişken eksikse (nutriscore_notu) modele veremeyeceğimiz için bu satırları düşüyoruz
    df = df.dropna(subset=['nutriscore_notu'])
    
    # Kullanılacak sütunlar ve eksik değerleri 'bilinmiyor' ile doldurma
    columns_to_fill = [
        'enerji_kcal', 'yag_g', 'seker_g', 'tuz_g', 'protein_g', 
        'lif_g', 'nova_grubu', 'kategori_listesi', 'markalar'
    ]
    
    for col in columns_to_fill:
        df[col] = df[col].fillna('bilinmiyor')
        
    # Her satırı metin formatına çeviren yardımcı fonksiyon
    def create_text(row):
        lif = str(row['lif_g'])
        lif_str = f"{lif}g" if lif != 'bilinmiyor' else 'bilinmiyor'
        return (f"Enerji: {row['enerji_kcal']}kcal, "
                f"Yağ: {row['yag_g']}g, "
                f"Şeker: {row['seker_g']}g, "
                f"Tuz: {row['tuz_g']}g, "
                f"Protein: {row['protein_g']}g, "
                f"Lif: {lif_str}, "
                f"Nova: {row['nova_grubu']}, "
                f"Kategori: {row['kategori_listesi']}, "
                f"Marka: {row['markalar']}")

    # BERT için 'text_feature' adında metinsel sütunu oluştur
    df['text_feature'] = df.apply(create_text, axis=1)
    
    # Nutriscore etiketleme (A:0, B:1, C:2, D:3, E:4)
    label_map = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}
    df['label'] = df['nutriscore_notu'].map(label_map)
    
    # Hatalı/Bilinmeyen harici Nutriscore notlarını düş (Örn: nan)
    df = df.dropna(subset=['label'])
    df['label'] = df['label'].astype(int)
    
    # Eğitim için sadece girdi metni ve hedef etiketi tut
    final_df = df[['text_feature', 'label']]
    
    # %80 Eğitim (Train), %20 Test bölünmesi (Stratified ile sınıfları dengeli bölüyoruz)
    train_df, test_df = train_test_split(
        final_df, 
        test_size=0.2, 
        random_state=42, 
        stratify=final_df['label']
    )
    
    # Dizin yoksa oluştur
    os.makedirs(output_dir, exist_ok=True)
    
    # Dosyaları kaydetme
    train_file = os.path.join(output_dir, 'train_data.csv')
    test_file = os.path.join(output_dir, 'test_data.csv')
    
    train_df.to_csv(train_file, index=False)
    test_df.to_csv(test_file, index=False)
    
    print("\n--- Veri Hazırlama Tamamlandı ---")
    print(f"Eğitim Seti (Train): {len(train_df)} satır -> {train_file}")
    print(f"Test Seti (Test): {len(test_df)} satır -> {test_file}\n")
    
    print("--- Örnek 3 Satır (Eğitim Setinden) ---")
    for idx, row in train_df.head(3).iterrows():
        print(f"METİN: {row['text_feature']}")
        print(f"ETİKET: {row['label']}\n")

if __name__ == '__main__':
    prepare_data()
