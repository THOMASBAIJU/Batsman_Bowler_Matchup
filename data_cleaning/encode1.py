import pandas as pd
from sklearn.preprocessing import LabelEncoder
import os

# Load the CSV file
file_path = 'ipl_batsman_bowler_summary_min_20_balls_set2.csv'

# Check if the input file exists
if not os.path.exists(file_path):
    print(f"Error: Input file '{file_path}' not found.")
    print("Please ensure the CSV file is in the same directory as the script, or provide the full path.")
    exit()

df = pd.read_csv(file_path)

print("Original DataFrame head:")
print(df.head())
print("\nOriginal DataFrame info:")
print(df.info())

# Initialize LabelEncoders for each column
le_batting_hand = LabelEncoder()
le_bowling_style = LabelEncoder()

# --- Apply Label Encoding to 'batting_hand' ---
df['batting_hand_encoded'] = le_batting_hand.fit_transform(df['batting_hand'])
print(f"\nUnique original batting_hand values: {le_batting_hand.classes_}")
print(f"Encoded batting_hand values: {list(range(len(le_batting_hand.classes_)))}")

# Generate and save batting_hand encoding details
batting_hand_mapping_df = pd.DataFrame({
    'Original_Value': le_batting_hand.classes_,
    'Encoded_Value': range(len(le_batting_hand.classes_))
})
batting_hand_mapping_filename = 'batting_hand_encoding_map.csv'
batting_hand_mapping_df.to_csv(batting_hand_mapping_filename, index=False)
print(f"Batting hand encoding details saved to '{batting_hand_mapping_filename}'")


# --- Apply Label Encoding to 'bowling_style' ---
df['bowling_style_encoded'] = le_bowling_style.fit_transform(df['bowling_style'])
print(f"\nUnique original bowling_style values: {le_bowling_style.classes_}")
print(f"Encoded bowling_style values: {list(range(len(le_bowling_style.classes_)))}")

# Generate and save bowling_style encoding details
bowling_style_mapping_df = pd.DataFrame({
    'Original_Value': le_bowling_style.classes_,
    'Encoded_Value': range(len(le_bowling_style.classes_))
})
bowling_style_mapping_filename = 'bowling_style_encoding_map.csv'
bowling_style_mapping_df.to_csv(bowling_style_mapping_filename, index=False)
print(f"Bowling style encoding details saved to '{bowling_style_mapping_filename}'")


# --- Remove the original categorical columns ---
# Use df.drop() to remove the columns. 'inplace=True' modifies the DataFrame directly.
# 'axis=1' specifies that we are dropping columns, not rows.
df.drop(columns=['batting_hand', 'bowling_style'], inplace=True)
print("\nOriginal 'batting_hand' and 'bowling_style' columns removed.")


# --- Save the main DataFrame with new encoded columns ---
output_filename = 'ipl_batsman_bowler_summary_encoded.csv'
df.to_csv(output_filename, index=False)

print(f"\nSuccessfully encoded 'batting_hand' and 'bowling_style'.")
print(f"New DataFrame head with encoded columns:")
print(df.head())
print(f"\nMain encoded data saved to '{output_filename}'")