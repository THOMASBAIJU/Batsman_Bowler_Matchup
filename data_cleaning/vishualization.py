import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load the dataset (make sure the path is correct)
df = pd.read_csv("final_dataset.csv")
# ---- HEATMAP: Total Runs (Top 10 Batsmen vs Top 10 Bowlers) ----
top_batsmen = df.groupby("batsman")["total_runs"].sum().nlargest(10).index
top_bowlers = df.groupby("bowler")["total_runs"].sum().nlargest(10).index

pivot_runs = df[df["batsman"].isin(top_batsmen) & df["bowler"].isin(top_bowlers)]
heatmap_data = pivot_runs.pivot_table(index="batsman", columns="bowler", values="total_runs", fill_value=0)

plt.figure(figsize=(12, 8))
sns.heatmap(heatmap_data, annot=True, fmt=".0f", cmap="YlOrRd", cbar_kws={"label": "Total Runs"})
plt.title("Top 10 Batsmen vs Top 10 Bowlers – Total Runs Heatmap")
plt.xlabel("Bowler")
plt.ylabel("Batsman")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# ---- GROUPED BAR PLOT: Dismissals per Batsman-Bowler Combo ----
# Get top 20 batsman-bowler pairs with most dismissals
top_dismissals = df.groupby(["batsman", "bowler"])["dismissals"].sum().reset_index()
top_dismissals = top_dismissals[top_dismissals["dismissals"] > 0]
top_dismissals = top_dismissals.sort_values("dismissals", ascending=False).head(20)

# Create a combo label
top_dismissals["matchup"] = top_dismissals["batsman"] + " vs " + top_dismissals["bowler"]

plt.figure(figsize=(14, 6))
sns.barplot(data=top_dismissals, x="matchup", y="dismissals")
plt.title("Top 20 Batsman-Bowler Matchups by Dismissals")
plt.xlabel("Matchup")
plt.ylabel("Dismissals")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# ---- HISTOGRAM: Dismissals Distribution ----
plt.figure(figsize=(10, 6))
sns.histplot(df["dismissals"], bins=30, kde=False, color="salmon", edgecolor="black")
plt.title("Distribution of Dismissals Across Matchups")
plt.xlabel("Number of Dismissals")
plt.ylabel("Number of Matchups")
plt.tight_layout()
plt.show()

# ---- HISTOGRAM: Dismissal Rate Distribution ----
plt.figure(figsize=(10, 6))
sns.histplot(df["dismissal_rate"], bins=30, kde=True, color="purple", edgecolor="black")
plt.title("Distribution of Dismissal Rates")
plt.xlabel("Dismissal Rate")
plt.ylabel("Density")
plt.tight_layout()
plt.show()

import seaborn as sns
import matplotlib.pyplot as plt

# ---- BOX PLOT: Strike Rate by Bowling Style ----
plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x='bowling_style_encoded', y='strike_rate')
plt.title("Strike Rate by Bowling Style (Boxplot)")
plt.xlabel("Bowling Style")
plt.ylabel("Strike Rate")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 6))
sns.barplot(data=df, x='bowling_style_encoded', y='dismissals')
plt.title("Total Dismissals by Bowling Style")
plt.xlabel("Bowling Style")
plt.ylabel("Total Dismissals")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()