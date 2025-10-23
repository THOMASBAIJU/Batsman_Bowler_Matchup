import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import joblib
import os

# --- Configuration ---
DATASET_PATH = "final_dataset.csv"
MODELS_DIR = "../models"
MODEL_FILENAME = os.path.join(MODELS_DIR, "rf_model_total_runs.joblib")

def train_batsman_model_rf():
    """
    Trains a Random Forest model to predict the total runs a batsman will score.
    This model is the responsibility of the Batsman Prediction Team.
    """
    print(" BATTING TEAM (Random Forest) SCRIPT ".center(60, "="))
    
    # --- 1. Load Data ---
    print(f"🔹 Loading dataset from '{DATASET_PATH}'...")
    os.makedirs(MODELS_DIR, exist_ok=True)
    try:
        df = pd.read_csv(DATASET_PATH)
    except FileNotFoundError:
        print(f"ERROR: Dataset not found. Please ensure '{DATASET_PATH}' is correct relative to your script location.")
        return

    # --- 2. Define Features and Target ---
    feature_columns = ['batsman', 'bowler', 'batting_hand', 'bowling_style', 'venue', 'total_balls']
    target_column = 'total_runs'
    
    X = df[feature_columns]
    y = df[target_column]
    print("Features and target defined for predicting runs.")

    # --- 3. Split Data ---
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(" Data split into training (80%) and testing (20%) sets.")

    # --- 4. Train Random Forest Regressor Model ---
    print(f"  Training RandomForestRegressor for '{target_column}'...")
    model = RandomForestRegressor(random_state=42, n_estimators=150, n_jobs=-1)
    model.fit(X_train, y_train)

    # --- 5. Evaluate and Save the Model ---
    preds = model.predict(X_test)
    print(f"   - Evaluation (R² Score): {r2_score(y_test, preds):.2f}")

    joblib.dump(model, MODEL_FILENAME)
    print(f" Model saved successfully to '{MODEL_FILENAME}'")
    print("=" * 60)

if __name__ == '__main__':
    train_batsman_model_rf()
