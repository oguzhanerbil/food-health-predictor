import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

plt.rcParams["font.family"] = "DejaVu Sans"

BG = "#f8fafc"
TEXT = "#0f172a"
MUTED = "#475569"
GRID = "#e2e8f0"

order = ["A", "B", "C", "D", "E"]
colors = {
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

x_min = df["protein_g"].min()
x_max = df["protein_g"].max()
x_grid = np.linspace(x_min, x_max, 500)

fig, ax = plt.subplots(figsize=(14, 8), facecolor=BG)
ax.set_facecolor(BG)

base_gap = 1.15

for i, grade in enumerate(order):
    subset = df.loc[df["nutriscore_notu"] == grade, "protein_g"].to_numpy()
    if len(subset) < 5:
        continue

    kde = gaussian_kde(subset)
    y = kde(x_grid)
    y = y / y.max()
    baseline = (len(order) - 1 - i) * base_gap

    ax.fill_between(
        x_grid,
        baseline,
        baseline + y,
        color=colors[grade],
        alpha=0.85,
        linewidth=0
    )
    ax.plot(x_grid, baseline + y, color="white", linewidth=1.5)

    median_val = np.median(subset)
    ax.scatter(median_val, baseline + 0.55, s=80, color="white", edgecolor=colors[grade], linewidth=2, zorder=5)
    ax.text(x_min - 1.5, baseline + 0.18, f"{grade}", fontsize=16, weight="bold", color=colors[grade], va="center")
    ax.text(x_max + 0.5, baseline + 0.18, f"medyan {median_val:.1f} g", fontsize=10, color=MUTED, va="center")

ax.set_title("Nutri-Score Katmanlarinda Protein Yogunlugu", fontsize=22, weight="bold", loc="left", color=TEXT, pad=18)
ax.text(x_min, base_gap * 4 + 1.15, "Her katman ilgili Nutri-Score grubunun protein dagilimini gosterir", fontsize=11, color=MUTED)

ax.set_xlabel("Protein (g)", fontsize=12, weight="bold", color=TEXT)
ax.set_ylabel("")
ax.set_yticks([])

ax.grid(axis="x", linestyle="--", color=GRID, alpha=0.6)
for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()
plt.show()
