import pandas as pd

# Load the CSV file
df = pd.read_csv('ipl_batsman_bowler_summary.csv')

filtered_df = df[df['total_balls'] >= 20]

print("Filtered Data - Head:")
print(filtered_df.head())

print("\nFiltered Data - Info:")
print(filtered_df.info())

output_filename = 'ipl_batsman_bowler_summary_min_20_balls set 2.csv'
filtered_df.to_csv(output_filename, index=False)
print(f"\nFiltered data saved to {output_filename}")
