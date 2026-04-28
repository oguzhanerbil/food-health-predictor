import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv("data/data.csv")

df = df.dropna(subset=["tuz_g", "nutriscore_notu"])

df = df[df["tuz_g"] < 15]

plt.figure(figsize=(8,6))

sns.boxplot(
    x="nutriscore_notu",
    y="tuz_g",
    data=df,
    order=["A","B","C","D","E"],
)

plt.title("Tuz Miktarı vs Nutriscore")
plt.xlabel("Nutriscore (A=İyi → E=Kötü)")
plt.ylabel("Tuz (g)")

plt.show()