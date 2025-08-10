import pandas as pd
from sklearn.preprocessing import LabelEncoder
import os

# --- Step 1: Load the CSV file ---
file_path = 'ipl_batsman_bowler_summary_min_20_balls set 2.csv'

if not os.path.exists(file_path):
    print(f"Error: Input file '{file_path}' not found.")
    exit()

df = pd.read_csv(file_path)

print("✅ Original DataFrame loaded successfully.\n")

# --- Step 2: Initialize LabelEncoders ---
le_batting_hand = LabelEncoder()
le_bowling_style = LabelEncoder()
le_batsman = LabelEncoder()
le_bowler = LabelEncoder()

# --- Step 3: Encode 'batting_hand' ---
df['batting_hand_encoded'] = le_batting_hand.fit_transform(df['batting_hand'])
pd.DataFrame({
    'Original_Value': le_batting_hand.classes_,
    'Encoded_Value': range(len(le_batting_hand.classes_))
}).to_csv('batting_hand_encoding_map.csv', index=False)
print("✅ 'batting_hand' encoded and map saved.")

# --- Step 4: Encode 'bowling_style' ---
df['bowling_style_encoded'] = le_bowling_style.fit_transform(df['bowling_style'])
pd.DataFrame({
    'Original_Value': le_bowling_style.classes_,
    'Encoded_Value': range(len(le_bowling_style.classes_))
}).to_csv('bowling_style_encoding_map.csv', index=False)
print("✅ 'bowling_style' encoded and map saved.")

# --- Step 5: Encode 'batsman' ---
df['batsman_encoded'] = le_batsman.fit_transform(df['batsman'])
pd.DataFrame({
    'Original_Value': le_batsman.classes_,
    'Encoded_Value': range(len(le_batsman.classes_))
}).to_csv('batsman_encoding_map.csv', index=False)
print("✅ 'batsman' encoded and map saved.")

# --- Step 6: Encode 'bowler' ---
df['bowler_encoded'] = le_bowler.fit_transform(df['bowler'])
pd.DataFrame({
    'Original_Value': le_bowler.classes_,
    'Encoded_Value': range(len(le_bowler.classes_))
}).to_csv('bowler_encoding_map.csv', index=False)
print("✅ 'bowler' encoded and map saved.")

# --- Step 7: Drop original categorical columns ---
df.drop(columns=['batting_hand', 'bowling_style', 'batsman', 'bowler'], inplace=True)
print("🗑️  Dropped original categorical columns.")

# --- Step 8: Save the encoded DataFrame ---
output_filename = 'ipl_batsman_bowler_summary_encoded.csv'
df.to_csv(output_filename, index=False)
print(f"\n✅ Final encoded dataset saved as '{output_filename}'.")


print("\n🔍 Preview of final encoded DataFrame:")
print(df.head())
