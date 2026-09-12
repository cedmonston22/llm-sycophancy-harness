import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

connection = sqlite3.connect("evals.db")

df = pd.read_sql_query(
    "SELECT model, turn, output_tokens, run_id, case_id, sample FROM results WHERE response IS NOT NULL",
    connection,
)

COLORS = {"gemini-3-flash-preview": "#2a78d6", "gpt-5": "#eb6834"}
NAMES = {"gemini-3-flash-preview": "Gemini 3 Flash", "gpt-5": "GPT-5"}

fig, ax = plt.subplots(figsize=(7, 4.5))

labeled = set()
for (run_id, case_id, model, sample), group in df.groupby(["run_id", "case_id", "model", "sample"]):
    by_turn = group.set_index("turn")["output_tokens"]
    label = NAMES[model] if model not in labeled else None
    labeled.add(model)
    ax.plot(
        [0, 1],
        [by_turn[1], by_turn[2]],
        color=COLORS[model],
        alpha=0.4,
        marker="o",
        markersize=3,
        label=label,
    )

ax.set_xticks([0, 1])
ax.set_xticklabels(["Answering", "Defending"])
ax.set_xlim(-0.15, 1.15)
ax.set_ylabel("output tokens")
ax.set_title("GPT-5 vs. Gemini Flash Output Tokens", loc="center", fontsize=13, pad=12)
ax.grid(axis="y", alpha=0.3)
ax.set_axisbelow(True)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(frameon=False, loc="upper left")

fig.tight_layout()
fig.savefig("tokens.png", dpi=160)
