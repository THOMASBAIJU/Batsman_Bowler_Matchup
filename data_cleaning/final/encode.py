import pandas as pd
from sklearn.preprocessing import LabelEncoder
import os

# Load dataset
file_path = "D:/Batsman_bowler_matchup/data_cleaning/final/final_dataset.csv"
df = pd.read_csv(file_path)
print("Original dataset shape:", df.shape)

# Columns that need encoding
categorical_cols = ['batsman', 'bowler', 'batting_hand', 'bowling_style', 'venue']

# Encode and save mappings
for col in categorical_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))  # replace with encoded values

    # Save mapping to CSV
    mapping_df = pd.DataFrame({
        "Original_Value": le.classes_,
        "Encoded_Value": range(len(le.classes_))
    })
    
    mapping_filename = f"D:/Batsman_bowler_matchup/data_cleaning/final/{col}_encoding_map.csv"
    mapping_df.to_csv(mapping_filename, index=False)
    print(f"✅ Mapping for '{col}' saved to {mapping_filename}")

# Save the fully encoded dataset
output_file = "D:/Batsman_bowler_matchup/data_cleaning/final/final_dataset_label_encoded.csv"
df.to_csv(output_file, index=False)

print(f"\n🎉 Encoding complete! Encoded dataset saved to {output_file}")
print("👉 Separate mapping CSVs also saved for each categorical column.")
