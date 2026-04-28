import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv("ilyas/data/model_veri.csv")

df["yag_g"] = df["yag_g"].fillna(0)

df = df[
    (df["yag_g"] >= 0) &
    (df["yag_g"] < 100)
]

df = df.dropna(subset=["nutriscore_notu"])

plt.figure(figsize=(8,6))

sns.boxplot(
    x="nutriscore_notu",
    y="yag_g",
    data=df,
    order=["A","B","C","D","E"]
)

plt.title("Yağ vs Nutriscore")
plt.xlabel("Nutriscore (A=İyi → E=Kötü)")
plt.ylabel("Yağ (g)")

plt.show()