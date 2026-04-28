import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams["font.family"] = "DejaVu Sans"
sns.set_theme(style="whitegrid")

BG = "#f8fafc"
TEXT = "#0f172a"
GRID = "#cbd5e1"

order = ["A", "B", "C", "D", "E"]
palette = {
    "A": "#16a34a",
    "B": "#84cc16",
    "C": "#eab308",
    "D": "#f97316",
    "E": "#dc2626"
}

df = pd.read_csv("ilyas/data/model_veri.csv")
df = df.dropna(subset=["nutriscore_notu", "protein_g"]).copy()
df = df[df["nutriscore_notu"].isin(order)].copy()
df["protein_g"] = pd.to_numeric(df["protein_g"], errors="coerce")
df = df.dropna(subset=["protein_g"]).copy()

q1 = df["protein_g"].quantile(0.01)
q99 = df["protein_g"].quantile(0.99)
df = df[df["protein_g"].between(q1, q99)].copy()

# groupby.apply kullanmadan örnekleme
samples = []
for grade in order:
    grp = df[df["nutriscore_notu"] == grade].copy()
    if len(grp) == 0:
        continue
    n = min(len(grp), 350)
    samples.append(grp.sample(n=n, random_state=42))

sample_df = pd.concat(samples, ignore_index=True)

fig, ax = plt.subplots(figsize=(13, 8), facecolor=BG)
ax.set_facecolor(BG)

sns.violinplot(
    data=df,
    x="nutriscore_notu",
    y="protein_g",
    order=order,
    hue="nutriscore_notu",
    palette=palette,
    inner=None,
    cut=0,
    linewidth=1.2,
    legend=False,
    ax=ax
)

sns.boxplot(
    data=df,
    x="nutriscore_notu",
    y="protein_g",
    order=order,
    width=0.18,
    showcaps=True,
    boxprops={"facecolor": "white", "zorder": 3},
    whiskerprops={"linewidth": 1.3},
    medianprops={"color": TEXT, "linewidth": 2},
    flierprops={"marker": ""},
    ax=ax
)

sns.stripplot(
    data=sample_df,
    x="nutriscore_notu",
    y="protein_g",
    order=order,
    hue="nutriscore_notu",
    palette=palette,
    dodge=False,
    alpha=0.22,
    size=3.2,
    jitter=0.25,
    legend=False,
    ax=ax
)

medians = df.groupby("nutriscore_notu")["protein_g"].median().reindex(order)
for i, grade in enumerate(order):
    value = medians[grade]
    ax.text(i, value + 0.7, f"medyan {value:.1f} g", ha="center", fontsize=10, color=TEXT, weight="bold")

ax.set_title("Nutri-Score Siniflarina Gore Protein Dagilimi", fontsize=22, weight="bold", loc="left", color=TEXT, pad=18)
ax.set_xlabel("Nutri-Score", fontsize=12, weight="bold", color=TEXT)
ax.set_ylabel("Protein (g)", fontsize=12, weight="bold", color=TEXT)

ax.grid(axis="y", linestyle="--", color=GRID, alpha=0.55)
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.show()
