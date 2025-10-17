import pandas as pd
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
import joblib
import os

# --- Configuration ---
DATASET_PATH = r"D:\Batsman_bowler_matchup\data_cleaning\final\final_dataset.csv"
MODELS_DIR = "models"

# --- 1. Load and Prepare the Data ---
print("🔹 Loading dataset...")
df = pd.read_csv(DATASET_PATH)

# MODIFIED: Feature Engineering for "Per-Ball" Metrics
print("🔹 Engineering 'per-ball' features for accurate predictions...")
# To avoid division by zero, replace 0s in 'total_balls' with 1
df['total_balls'] = df['total_balls'].replace(0, 1)
df['runs_per_ball'] = df['total_runs'] / df['total_balls']

# Ensure 'dismissals' is binary (0 or 1)
df['dismissals'] = (df['dismissals'] > 0).astype(int)
print("✅ 'runs_per_ball' created and 'dismissals' converted to binary.")

# --- 2. Define Features and Targets ---
# The inputs to the model remain the same
feature_columns = ['batsman', 'bowler', 'total_balls', 'batting_hand', 'bowling_style', 'venue']
X = df[feature_columns]

# MODIFIED: The targets now include our new 'runs_per_ball' metric
target_columns = ["runs_per_ball", "dismissals", "strike_rate", "dismissal_rate"]
y = df[target_columns]

# --- 3. Split Data ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
print("🔹 Data split into training and testing sets.")

# --- 4. Train Models ---
for target in target_columns:
    print("-" * 30)
    
    model_name_suffix = target # 'runs_per_ball' will be part of the filename
    if target == "runs_per_ball":
        # Rename the output model to 'total_runs' for consistency with the app
        model_name_suffix = "total_runs"

    if target == "dismissals":
        print(f"☑️  Training XGBClassifier for '{target}'...")
        model = XGBClassifier(objective='binary:logistic', eval_metric='logloss', use_label_encoder=False, random_state=42)
    else:
        print(f"☑️  Training XGBRegressor for '{target}'...")
        model = XGBRegressor(random_state=42)

    model.fit(X_train, y_train[target])
    
    # Save the model
    model_filename = os.path.join(MODELS_DIR, f"xgb_model_{model_name_suffix}.joblib")
    joblib.dump(model, model_filename)
    print(f"✅ Model for '{model_name_suffix}' saved to '{model_filename}'")
    
    # Evaluate
    preds = model.predict(X_test)
    if target == "dismissals":
        print(f"  Accuracy: {accuracy_score(y_test[target], preds):.2f}")
    else:
        print(f"  R² Score: {r2_score(y_test[target], preds):.2f}")
    print("-" * 30 + "\n")

print("🎉 All models have been retrained with the correct logic and saved.")
