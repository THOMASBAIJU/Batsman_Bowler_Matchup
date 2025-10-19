import pandas as pd
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score
import joblib
import os

# --- Configuration ---
# CORRECTED: Added '../' to go up one directory to find the dataset
DATASET_PATH = "../final_dataset.csv"
MODELS_DIR = "../models" # Also correct this path to save models in the main models folder

# --- 1. Load and Prepare the Data ---
print("🔹 Loading dataset...")
# Create the models directory if it doesn't exist at the correct location
os.makedirs(MODELS_DIR, exist_ok=True)

df = pd.read_csv(DATASET_PATH)

print("🔹 Preparing data for training...")
# Ensure 'dismissals' is binary (0 or 1)
df['dismissals'] = (df['dismissals'] > 0).astype(int)
print("✅ 'dismissals' converted to binary.")

# --- 2. Define Features and Targets ---
feature_columns = ['batsman', 'bowler', 'total_balls', 'batting_hand', 'bowling_style', 'venue']
X = df[feature_columns]

target_columns = ["total_runs", "dismissals", "strike_rate", "dismissal_rate"]
y = df[target_columns]

# --- 3. Split Data ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
print("🔹 Data split into training and testing sets.")

# --- 4. Train Models ---
for target in target_columns:
    print("-" * 30)
    
    model_name_suffix = target

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