import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def remove_outliers_iqr_and_save(dataframe_path, column_name, output_path=None):
    """
    Removes outliers from a specified column of a DataFrame using the IQR method,
    and then saves the cleaned DataFrame.

    Args:
        dataframe_path (str): The file path to the input CSV DataFrame.
        column_name (str): The name of the column to clean.
        output_path (str, optional): The file path to save the cleaned CSV.
                                     If None, it overwrites the original file.
    """
    try:
        df_original = pd.read_csv(dataframe_path)
        print(f"Original dataset loaded from '{dataframe_path}'. Shape: {df_original.shape}")
    except FileNotFoundError:
        print(f"Error: '{dataframe_path}' not found. Please check the path.")
        return
    except Exception as e:
        print(f"An error occurred while loading the dataset: {e}")
        return

    if column_name not in df_original.columns:
        print(f"Error: Column '{column_name}' not found in the DataFrame. No outliers removed.")
        return
    
    # Check if the column is numeric before calculating IQR
    if not pd.api.types.is_numeric_dtype(df_original[column_name]):
        print(f"Error: Column '{column_name}' is not numeric. IQR method cannot be applied.")
        print("Outlier removal skipped.")
        return

    Q1 = df_original[column_name].quantile(0.25)
    Q3 = df_original[column_name].quantile(0.75)
    IQR = Q3 - Q1
    
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    print(f"Calculated bounds for '{column_name}': Lower={lower_bound}, Upper={upper_bound}")

    # Filter out rows where the column value is outside the bounds
    df_cleaned = df_original[(df_original[column_name] >= lower_bound) & (df_original[column_name] <= upper_bound)]
    
    num_removed = len(df_original) - len(df_cleaned)
    print(f"Removed {num_removed} outliers from '{column_name}' using IQR method.")
    print(f"Cleaned dataset shape: {df_cleaned.shape}")

    # Determine the output path
    if output_path is None:
        final_output_path = dataframe_path # Overwrite original
        print(f"Overwriting original file: '{final_output_path}' with cleaned data.")
    else:
        final_output_path = output_path
        print(f"Saving cleaned data to: '{final_output_path}'")

    # Save the cleaned DataFrame to CSV
    df_cleaned.to_csv(final_output_path, index=False)
    print("Cleaned data saved successfully.")

def visualize_boxplot(dataframe, column_name, title_suffix="", x_label=""):
    """
    Generates a box plot for a specified column of a DataFrame.
    """
    if column_name not in dataframe.columns:
        print(f"Error: Column '{column_name}' not found in the DataFrame for visualization.")
        return
        
    if not pd.api.types.is_numeric_dtype(dataframe[column_name]):
        print(f"Cannot create boxplot: Column '{column_name}' is not numeric.")
        return

    plt.figure(figsize=(8, 6))
    sns.boxplot(y=dataframe[column_name], color='lightblue', medianprops={'color': 'blue'})

    plt.title(f"{column_name} {title_suffix}")
    plt.ylabel(column_name)
    plt.xticks([0], [x_label])
    plt.grid(axis='y', linestyle='-')
    plt.show()

# --- Main execution ---
if __name__ == "__main__":
    DATASET_PATH = "Full dataset.csv"
    
    # --- THIS IS THE MODIFIED LINE ---
    COLUMN_TO_CLEAN = 'Wickets Taken' # The column you want to clean outliers from

    # --- Step 1: Visualize BEFORE outlier removal ---
    try:
        df_before_cleaning = pd.read_csv(DATASET_PATH)
        visualize_boxplot(df_before_cleaning, COLUMN_TO_CLEAN, 
                          title_suffix="- Before Removing Outliers", 
                          x_label="Before Outlier Removal")
    except FileNotFoundError:
        print(f"Cannot visualize before cleaning: '{DATASET_PATH}' not found.")
    except Exception as e:
        print(f"An error occurred during pre-cleaning visualization: {e}")

    # --- Step 2: Remove outliers and save the cleaned data ---
    print("\n--- Starting Outlier Removal Process ---")
    remove_outliers_iqr_and_save(DATASET_PATH, COLUMN_TO_CLEAN, output_path=DATASET_PATH) # Overwrites original
    print("--- Outlier Removal Process Completed ---")

    # --- Step 3: Visualize AFTER outlier removal (load the now-modified CSV) ---
    try:
        df_after_cleaning = pd.read_csv(DATASET_PATH)
        visualize_boxplot(df_after_cleaning, COLUMN_TO_CLEAN, 
                          title_suffix="- After Removing Outliers", 
                          x_label="After Outlier Removal")
    except FileNotFoundError:
        print(f"Cannot visualize after cleaning: '{DATASET_PATH}' not found (this should not happen after saving).")
    except Exception as e:
        print(f"An error occurred during post-cleaning visualization: {e}")