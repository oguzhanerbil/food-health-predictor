import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv("data/data.csv")
print(df["nova_grubu"].value_counts())
df = df.dropna(subset=["nova_grubu", "nutriscore_notu"])

plt.figure(figsize=(8,6))

sns.countplot(
    x="nova_grubu",
    hue="nutriscore_notu",
    data=df,
    hue_order=["A","B","C","D","E"]
)

plt.title("NOVA vs Nutriscore Dağılımı")
plt.xlabel("NOVA (1=Doğal → 4=Ultra İşlenmiş)")
plt.ylabel("Ürün Sayısı")

plt.legend(title="Nutriscore")

plt.show()