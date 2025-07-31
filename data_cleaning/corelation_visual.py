import seaborn as sns
import matplotlib.pyplot as plt

import pandas as pd
df= pd.read_csv("final_dataset.csv")
# ---- SELECT ONLY NUMERIC COLUMNS ----
numeric_df = df.select_dtypes(include=['float64', 'int64'])

# ---- COMPUTE CORRELATION MATRIX ----
corr_matrix = numeric_df.corr()

# ---- PLOT HEATMAP ----
plt.figure(figsize=(12, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5, square=True)
plt.title("Correlation Heatmap of Numeric Features")
plt.tight_layout()
plt.show()
