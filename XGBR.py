import pandas as pd
import xgboost as xgb # Imported for plotting functionality
import matplotlib.pyplot as plt # Imported to create and save the plot
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import joblib
import os

# --- Configuration ---
DATASET_PATH = r"D:\Batsman_bowler_matchup\data_cleaning\final\final_dataset.csv"
MODELS_DIR = "models"
PLOTS_DIR = "plots" # ADDED: Directory to save the tree plots

# ADDED: Create directories if they don't already exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)

# --- 1. Load and Prepare the Data ---
print("🔹 Loading dataset...")
df = pd.read_csv(DATASET_PATH)

# Feature Engineering for "Per-Ball" Metrics
print("🔹 Engineering 'per-ball' features for accurate predictions...")
# To avoid division by zero, replace 0s in 'total_balls' with 1
df['total_balls'] = df['total_balls'].replace(0, 1)
df['runs_per_ball'] = df['total_runs'] / df['total_balls']
print("✅ 'runs_per_ball' feature created.")

# --- 2. Define Features and Targets ---
# The inputs to the model
feature_columns = ['batsman', 'bowler', 'total_balls', 'batting_hand', 'bowling_style', 'venue']
X = df[feature_columns]

# The targets now only include the regression tasks.
target_columns = ["runs_per_ball", "strike_rate", "dismissal_rate"]
y = df[target_columns]

# --- 3. Split Data ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
print("🔹 Data split into training and testing sets.")

# --- 4. Train a Regressor Model for Each Target ---
for target in target_columns:
    print("-" * 30)
    
    model_name_suffix = target
    if target == "runs_per_ball":
        # Rename the output model to 'total_runs' for consistency with the app
        model_name_suffix = "total_runs"

    # This script now only trains XGBRegressor models
    print(f"☑️  Training XGBRegressor for '{target}'...")
    # Using xgb.XGBRegressor to align with import for plotting
    model = xgb.XGBRegressor(random_state=42)

    model.fit(X_train, y_train[target])
    
    # Save the model
    model_filename = os.path.join(MODELS_DIR, f"xgb_model_{model_name_suffix}.joblib")
    joblib.dump(model, model_filename)
    print(f"✅ Model for '{model_name_suffix}' saved to '{model_filename}'")
    
    # Evaluate the model's performance
    preds = model.predict(X_test)
    print(f"   R² Score: {r2_score(y_test[target], preds):.2f}")

    # --- CODE ADDED TO PLOT GRAPH ---
    print(f"📊 Plotting the first decision tree for '{target}'...")
    try:
        # Set a large figure size for better readability of the tree
        fig, ax = plt.subplots(figsize=(30, 15))
        
        # FIXED: Changed deprecated 'num_trees' to 'tree_idx' to resolve the warning.
        xgb.plot_tree(model, tree_idx=0, ax=ax)
        plt.title(f"Decision Tree for {model_name_suffix} (First Tree)", fontsize=25)

        # Save the plot to a file in the plots directory
        plot_filename = os.path.join(PLOTS_DIR, f"tree_plot_{model_name_suffix}.png")
        plt.savefig(plot_filename, dpi=100, bbox_inches='tight')
        print(f"✅ Tree plot saved to '{plot_filename}'")

    except Exception as e:
        print(f"⚠️ Could not plot tree. Ensure Graphviz is installed and in your system's PATH. Error: {e}")
    finally:
        # Close the plot to free up memory before the next loop iteration
        plt.close(fig)
    # --- END OF ADDED CODE ---
    
    print("-" * 30 + "\n")

print("🎉 All XGBoost regression models have been trained and saved successfully!")

