"""
MIS20070 Digital Society: Higher Ground 2060
Reads the survey responses exported from Google Sheets (responses.xlsx)
and aggregates them into a single ternary plot, with every response shown as a dot.

Vertices: Efficiency (top), Community (bottom left), Safety (bottom right).
Each response is three shares that add up to 1 (e.g. 0.5 / 0.3 / 0.2).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------- 1. Load the data ----------
df = pd.read_excel("responses.xlsx", sheet_name="Responses")

# Exclude answers flagged as a possible duplicate (same device answering twice)
df = df[df["possible_duplicate"] != "yes"]

# ---------- 2. Check the data is valid ----------
values = df[["efficiency", "community", "safety"]]
assert values.min().min() >= 0 and values.max().max() <= 1, "Values must be between 0 and 1"
assert np.allclose(values.sum(axis=1), 1, atol=0.001), "Each response must add up to 1"
assert df.duplicated(subset=["respondent_id", "plot"]).sum() == 0, "Duplicate responses found"

present = df[df["plot"] == "present"]
future = df[df["plot"] == "future"]
print(f"Present-day responses: {len(present)}")
print(f"2060 responses:        {len(future)}")

# ---------- 3. Convert ternary values to x, y coordinates ----------
# Community corner = (0, 0), Safety corner = (1, 0), Efficiency corner = (0.5, 0.866)
def to_xy(data):
    x = data["safety"] + 0.5 * data["efficiency"]
    y = (np.sqrt(3) / 2) * data["efficiency"]
    return x, y

# ---------- 4. Draw the triangle and gridlines ----------
fig, ax = plt.subplots(figsize=(8, 7.5))
corners = np.array([[0, 0], [1, 0], [0.5, np.sqrt(3) / 2], [0, 0]])
ax.plot(corners[:, 0], corners[:, 1], color="black", linewidth=1.5)

for f in np.arange(0.1, 1.0, 0.1):  # gridlines every 10%
    for a, b in [({"efficiency": f, "community": 1 - f, "safety": 0}, {"efficiency": f, "community": 0, "safety": 1 - f}),
                 ({"efficiency": 1 - f, "community": f, "safety": 0}, {"efficiency": 0, "community": f, "safety": 1 - f}),
                 ({"efficiency": 1 - f, "community": 0, "safety": f}, {"efficiency": 0, "community": 1 - f, "safety": f})]:
        x1, y1 = to_xy(pd.Series(a)); x2, y2 = to_xy(pd.Series(b))
        ax.plot([x1, x2], [y1, y2], color="lightgrey", linewidth=0.6, zorder=0)

ax.text(0.5, np.sqrt(3) / 2 + 0.04, "Efficiency", ha="center", fontsize=13, fontweight="bold")
ax.text(-0.04, -0.05, "Community", ha="center", fontsize=13, fontweight="bold")
ax.text(1.04, -0.05, "Safety", ha="center", fontsize=13, fontweight="bold")

# ---------- 5. Plot every response as a dot ----------
x, y = to_xy(present)
ax.scatter(x, y, s=45, color="#7c8582", alpha=0.75, edgecolor="white", label=f"2026 (today), n = {len(present)}")
x, y = to_xy(future)
ax.scatter(x, y, s=45, color="#b4502f", alpha=0.75, edgecolor="white", label=f"2060 (future), n = {len(future)}")

# Average position for each period, with an arrow showing the shift
mp, mf = present[["efficiency", "community", "safety"]].mean(), future[["efficiency", "community", "safety"]].mean()
(px, py), (fx, fy) = to_xy(mp), to_xy(mf)
ax.annotate("", xy=(fx, fy), xytext=(px, py), arrowprops=dict(arrowstyle="->", color="black", lw=2))
ax.scatter([px, fx], [py, fy], s=160, marker="X", color=["#4a5553", "#8a3a20"], edgecolor="black", zorder=5, label="Average position")

print("\nAverage priority (2026 -> 2060):")
for v in ["efficiency", "community", "safety"]:
    print(f"  {v.capitalize():<11} {mp[v]:.0%} -> {mf[v]:.0%}")

ax.set_title("How society balances efficiency, community and safety: 2026 vs 2060", fontsize=13, pad=28)
ax.legend(loc="upper right", frameon=False)
ax.set_aspect("equal")
ax.axis("off")
plt.tight_layout()
plt.savefig("aggregated_ternary_plot.png", dpi=200)
plt.show()
