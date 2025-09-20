import pandas as pd

# Load both datasets
final_df = pd.read_csv("D:/Batsman_bowler_matchup/data_cleaning/final/Final_dataset.csv")
cleaned_df = pd.read_csv("D:/Batsman_bowler_matchup/data_cleaning/final/Final_dataset_cleaned.csv")

print("Final dataset columns:", final_df.columns)
print("Cleaned dataset columns:", cleaned_df.columns)

# Merge batting_hand and bowling_style from Final_dataset into Final_dataset_cleaned
merged_df = cleaned_df.merge(
    final_df[['batsman', 'bowler', 'batting_hand', 'bowling_style']],
    on=['batsman', 'bowler'],
    how='left'
)

# Save new combined dataset
output_file = "D:/Batsman_bowler_matchup/data_cleaning/final/Final_dataset_cleaned_with_styles.csv"
merged_df.to_csv(output_file, index=False)

print(f"✅ Merged dataset saved to {output_file}")
print("New dataset shape:", merged_df.shape)
print("Columns:", merged_df.columns)
