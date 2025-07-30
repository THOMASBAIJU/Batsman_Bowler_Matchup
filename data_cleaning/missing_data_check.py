import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("data_cleaning/final_dataset.csv")

def plot_missing_data(df):
    """
    Plots the percentage of missing data for each column in the DataFrame.
    """
    if df.empty:
        print("The DataFrame is empty. No data to plot.")
        return

    missing_data = df.isnull().mean() * 100
    missing_data = missing_data[missing_data > 0].sort_values(ascending=False)

    if missing_data.empty:
        print("No missing data to plot.")
        return
 
    plt.figure(figsize=(10, 6))
    sns.barplot(x=missing_data.index, y=missing_data.values, palette='viridis')
    plt.xticks(rotation=45)
    plt.title('Percentage of Missing Data by Column')
    plt.xlabel('Columns')
    plt.ylabel('Percentage of Missing Data (%)')
    plt.tight_layout()
    plt.show()
    print("Missing data plot generated successfully.")

# Call the function
plot_missing_data(df)

    