import pandas as pd

# --- Configuration ---
# The raw, uncleaned dataset with all original columns.
# This should be the output from your 'venue.py' or initial data gathering script.
RAW_DATASET_PATH = "Final_dataset.csv" 

# The name of the final, clean output file the rest of your app will use.
FINAL_OUTPUT_PATH = "final_dataset.csv" 

def remove_outliers_iqr(data, column):
    """Removes outliers from a specific column in a DataFrame using the IQR method."""
    Q1 = data[column].quantile(0.25)
    Q3 = data[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    # Return a filtered DataFrame containing only the rows within the bounds
    return data[(data[column] >= lower_bound) & (data[column] <= upper_bound)]

def main():
    """
    Consolidated script to load the raw dataset, remove outliers from key
    metric columns, and save the final, clean dataset.
    """
    print("🔹 Starting consolidated data preparation process...")
    
    try:
        # Step 1: Load the original, complete dataset
        df = pd.read_csv(RAW_DATASET_PATH)
        print(f"✅ Loaded raw dataset '{RAW_DATASET_PATH}' with {len(df)} rows.")
    except FileNotFoundError:
        print(f"❌ ERROR: Raw dataset not found at '{RAW_DATASET_PATH}'. Please ensure the file exists.")
        return

    # Step 2: Define columns for outlier removal
    numeric_cols_for_cleaning = ['total_runs', 'dismissals', 'strike_rate', 'dismissal_rate']
    
    # Step 3: Sequentially remove outliers for each column
    # The DataFrame is filtered in place, ensuring all columns are preserved for the valid rows.
    for col in numeric_cols_for_cleaning:
        rows_before = len(df)
        if col in df.columns:
            df = remove_outliers_iqr(df, col)
            rows_after = len(df)
            print(f"   - Removed {rows_before - rows_after} outliers based on '{col}'.")
        else:
            print(f"   ⚠️ WARNING: Column '{col}' not found. Skipping outlier removal for this column.")

    # Step 4: Save the final, clean dataset
    # This single output file is now ready for the encoding and model training steps.
    df.to_csv(FINAL_OUTPUT_PATH, index=False)
    
    print("\n🎉 Consolidated cleaning complete!")
    print(f"✅ Final dataset saved as '{FINAL_OUTPUT_PATH}' with {len(df)} rows.")
    print("   This file now contains all necessary columns and is ready for use.")

if __name__ == "__main__":
    main()