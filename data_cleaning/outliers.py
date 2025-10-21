import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def visualize_outliers_boxplot(dataframe, column_name, title_prefix=""):
    """
    Generates a box plot to visualize outliers in a specified column of a DataFrame.

    Args:
        dataframe (pd.DataFrame): The input DataFrame.
        column_name (str): The name of the column to visualize.
        title_prefix (str, optional): A prefix for the plot title (e.g., "Before Removing Outliers").
    """
    if column_name not in dataframe.columns:
        print(f"Error: Column '{column_name}' not found in the DataFrame.")
        return

    plt.figure(figsize=(8, 6))
    
    # Create the box plot
    sns.boxplot(y=dataframe[column_name], color='lightblue', medianprops={'color': 'blue'})

    # Calculate quartiles and IQR to identify specific outliers for custom plotting
    Q1 = dataframe[column_name].quantile(0.25)
    Q3 = dataframe[column_name].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Filter for outliers
    outliers = dataframe[(dataframe[column_name] < lower_bound) | (dataframe[column_name] > upper_bound)][column_name]
    
    # Plot individual outliers as dots, similar to your example image
    if not outliers.empty:
        # Get x-axis coordinates for scattering (boxplot is at x=0)
        x_coords = np.random.normal(0, 0.04, size=len(outliers)) 
        plt.scatter(x_coords, outliers, color='black', edgecolor='white', linewidth=1, label='Outliers (Dots)', zorder=5)

    # Custom legend elements for box and outliers
    handles = [
        plt.Line2D([0], [0], color='lightblue', marker='s', markersize=10, label='Useful Data (Box)'),
        plt.Line2D([0], [0], color='black', marker='o', linestyle='None', markersize=7, markeredgecolor='white', markeredgewidth=1, label='Outliers (Dots)')
    ]
    plt.legend(handles=handles, loc='upper right')

    plt.title(f"{column_name} - {title_prefix}")
    plt.ylabel(column_name)
    plt.xticks([0], ["Before Outlier Removal"]) # Set a single tick label for the x-axis
    plt.grid(axis='y', linestyle='-')
    plt.show()

# --- Example Usage ---
if __name__ == "__main__":
    # Load your dataset
    try:
        df = pd.read_csv("ipl_batsman_bowler_summary_min_20_balls set 2.csv")
        print("Dataset loaded successfully.")
        print(df.head())

        # Visualize outliers for 'total_runs'
        visualize_outliers_boxplot(df, 'total_runs', title_prefix="Before Removing Outliers")

        # You can call it for other columns if needed, for example 'strike_rate'
        # visualize_outliers_boxplot(df, 'strike_rate', title_prefix="Before Removing Outliers")

    except FileNotFoundError:
        print("Error: 'final_dataset.csv' not found. Please make sure the file is in the same directory.")
    except Exception as e:
        print(f"An error occurred: {e}")