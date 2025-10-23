import os
import json
import pandas as pd

# Paths
input_folder = "D:/Batsman_bowler_matchup/ipl last 5 season/"
output_file = "D:/Batsman_bowler_matchup/data_cleaning/final/Final_dataset_cleaned.csv"

all_data = []

# Read JSON files
for file in os.listdir(input_folder):
    if file.endswith(".json"):
        file_path = os.path.join(input_folder, file)
        print(f"Reading {file_path} ...")
        with open(file_path, "r") as f:
            data = json.load(f)

        venue = data["info"].get("venue", "Unknown Venue")

        for innings in data.get("innings", []):
            for over in innings.get("overs", []):
                for delivery in over.get("deliveries", []):
                    batsman = delivery["batter"]
                    bowler = delivery["bowler"]
                    runs_off_bat = delivery["runs"]["batter"]
                    wicket = 1 if "wickets" in delivery else 0

                    all_data.append({
                        "batsman": batsman,
                        "bowler": bowler,
                        "venue": venue,
                        "runs_off_bat": runs_off_bat,
                        "is_wicket": wicket
                    })

# Convert to DataFrame
df = pd.DataFrame(all_data)
print(f"Raw merged data: {df.shape}")
print(df.head())

# Step 1: Calculate total balls per batsman-bowler pair
pair_totals = df.groupby(["batsman", "bowler"]).agg(
    total_balls=("runs_off_bat", "count")
).reset_index()

# Step 2: Keep only pairs with >=20 balls
valid_pairs = pair_totals[pair_totals["total_balls"] >= 20][["batsman", "bowler"]]

# Step 3: Merge back to original data (keeping venue info)
df_filtered = df.merge(valid_pairs, on=["batsman", "bowler"], how="inner")

# Step 4: Aggregate with venue included
matchup = df_filtered.groupby(["batsman", "bowler", "venue"]).agg(
    total_runs=("runs_off_bat", "sum"),
    total_balls=("runs_off_bat", "count"),
    dismissals=("is_wicket", "sum")
).reset_index()

# Step 5: Add rates
matchup["strike_rate"] = (matchup["total_runs"] / matchup["total_balls"]) * 100
matchup["dismissal_rate"] = (matchup["dismissals"] / matchup["total_balls"]) * 100

# Save final CSV
matchup.to_csv(output_file, index=False, encoding="utf-8-sig")
print(f"\n✅ Cleaned dataset with venue saved to {output_file}")
print(f"Final shape: {matchup.shape}")
print(matchup.head(10))
