import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


df = pd.read_csv("ilyas/data/model_veri.csv")


score_map = {"A":1, "B":2, "C":3, "D":4, "E":5}
df["score_num"] = df["nutriscore_notu"].map(score_map)

df["seker_g"] = df["seker_g"].fillna(0)


df = df[
    (df["seker_g"] >= 0) &
    (df["seker_g"] < 100)
]


df = df.dropna(subset=["nutriscore_notu"])


plt.figure(figsize=(8,6))

sns.boxplot(
    x="nutriscore_notu",
    y="seker_g",
    data=df,
    order=["A", "B", "C", "D", "E"]
)

plt.title("Şeker Miktarı vs Nutriscore")
plt.xlabel("Nutriscore (A=İyi → E=Kötü)")
plt.ylabel("Şeker (g)")

plt.show()