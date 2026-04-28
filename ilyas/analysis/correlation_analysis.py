import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv("data/data.csv")

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

df = df[cols].dropna()

corr = df.corr()

plt.figure(figsize=(10,8))

sns.heatmap(
    corr,
    annot=True,
    cmap="coolwarm",
    fmt=".2f"
)

plt.title("Korelasyon Matrisi")
plt.show()