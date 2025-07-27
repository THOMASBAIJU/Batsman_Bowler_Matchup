import pandas as pd

# Load the Excel file
df = pd.read_csv("ipl_batsman_bowler_summary_encoded.csv")

# Delete a column (e.g., 'ColumnName')
df.drop(['batting_hand', 'bowling_style'], axis=1, inplace=True)


# Save it back to Excel
df.to_csv("final_dataset.csv", index=False)
