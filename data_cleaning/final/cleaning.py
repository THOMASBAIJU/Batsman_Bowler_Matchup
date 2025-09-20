import pandas as pd

# Load dataset
df = pd.read_csv("Final_dataset.csv")

# Columns where we want to remove outliers
numeric_cols = ['total_runs', 'dismissals', 'strike_rate', 'dismissal_rate']

# Function to remove outliers using IQR
def remove_outliers_iqr(data, column):
    Q1 = data[column].quantile(0.25)
    Q3 = data[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return data[(data[column] >= lower) & (data[column] <= upper)]

# Apply outlier removal for each numeric column
for col in numeric_cols:
    before = len(df)
    df = remove_outliers_iqr(df, col)
    after = len(df)
    print(f"Removed {before - after} outliers from '{col}'")

# Save cleaned dataset
output_file = "Final_dataset_cleaned.csv"
df.to_csv(output_file, index=False)

print(f"\n✅ Cleaned dataset saved as '{output_file}' with {len(df)} rows.")
