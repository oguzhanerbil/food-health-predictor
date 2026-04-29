import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# =========================
# 📥 VERİ
# =========================
df = pd.read_csv("data/data.csv")

# Nutriscore sıralama
order = ["A","B","C","D","E"]

# =========================
# 📊 1. ŞEKER ANALİZİ (BOXPLOT)
# =========================
plt.figure(figsize=(8,6))

sns.boxplot(
    x="nutriscore_notu",
    y="seker_g",
    data=df,
    order=order,
    showfliers=False
)

plt.title("Şeker vs Nutriscore")
plt.xlabel("Nutriscore (A=İyi → E=Kötü)")
plt.ylabel("Şeker (g)")
plt.show()

# =========================
# 📊 2. YAĞ ANALİZİ
# =========================
plt.figure(figsize=(8,6))

sns.boxplot(
    x="nutriscore_notu",
    y="yag_g",
    data=df,
    order=order,
    showfliers=False
)

plt.title("Yağ vs Nutriscore")
plt.show()

# =========================
# 📊 3. TUZ ANALİZİ
# =========================
plt.figure(figsize=(8,6))

sns.boxplot(
    x="nutriscore_notu",
    y="tuz_g",
    data=df,
    order=order,
    showfliers=False
)

plt.title("Tuz vs Nutriscore")
plt.show()

# =========================
# 📊 4. ŞEKERLİ ÜRÜN ANALİZİ
# =========================
df["sekerli"] = df["seker_g"] > 10

cross = pd.crosstab(df["sekerli"], df["nutriscore_notu"], normalize="index")
cross = cross[order]

cross.plot(kind="bar", stacked=True)

plt.title("Şekerli Ürün vs Nutriscore (%)")
plt.xlabel("Şekerli mi?")
plt.ylabel("Oran")
plt.legend(title="Nutriscore")
plt.show()

# =========================
# 📊 5. PALM YAĞI ANALİZİ
# =========================
cross = pd.crosstab(df["palmiye_yagi_icermez"], df["nutriscore_notu"], normalize="index")
cross = cross[order]

cross.plot(kind="bar", stacked=True)

plt.title("Palm Yağına Göre Nutriscore (%)")
plt.xlabel("Palm yağı içermez mi?")
plt.ylabel("Oran")
plt.show()

# =========================
# 📊 6. NOVA (İŞLENMİŞLİK)
# =========================
cross = pd.crosstab(df["nova_grubu"], df["nutriscore_notu"], normalize="index")
cross = cross[order]

cross.plot(kind="bar", stacked=True)

plt.title("NOVA Grubu vs Nutriscore (%)")
plt.xlabel("NOVA (1=Doğal → 4=Ultra işlenmiş)")
plt.ylabel("Oran")
plt.show()

# =========================
# 📊 7. KORELASYON
# =========================

# sayıya çevir
score_map = {"A":1, "B":2, "C":3, "D":4, "E":5}
df["score_num"] = df["nutriscore_notu"].map(score_map)

cols = [
    "enerji_kcal",
    "yag_g",
    "doymus_yag_g",
    "karbonhidrat_g",
    "seker_g",
    "protein_g",
    "tuz_g",
    "lif_g",
    "score_num"
]

corr_df = df[cols].dropna()
corr = corr_df.corr()

# isim düzelt
corr = corr.rename(
    index={"score_num": "Nutriscore"},
    columns={"score_num": "Nutriscore"}
)

plt.figure(figsize=(10,8))

sns.heatmap(
    corr,
    annot=True,
    cmap="coolwarm",
    fmt=".2f"
)

plt.title("Korelasyon Matrisi")
plt.show()