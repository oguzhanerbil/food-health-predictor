import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv("ilyas/data/model_veri.csv")


score_map = {"A":1, "B":2, "C":3, "D":4, "E":5}
df["score_num"] = df["nutriscore_notu"].map(score_map)


df["protein_g"] = df["protein_g"].fillna(0)


df = df[
    (df["protein_g"] > 0) &    
    (df["protein_g"] < 50)     
]


df = df.dropna(subset=["score_num"])


print("\n📊 Nutriscore dağılımı:")
print(df["nutriscore_notu"].value_counts())

print("\n📊 Ortalama protein:")
print(df.groupby("nutriscore_notu")["protein_g"].mean())


plt.figure()

sns.boxplot(
    x="nutriscore_notu",
    y="protein_g",
    data=df,
    order=["A","B","C","D","E"]  
)
plt.title("Nutriscore'a Göre Protein Dağılımı")

plt.show()