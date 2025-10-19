import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import joblib
import os

# --- Configuration ---
DATASET_PATH = "../final_dataset.csv"
MODELS_DIR = "../models"
MODEL_FILENAME = os.path.join(MODELS_DIR, "xgb_model_dismissals.joblib")

def train_bowler_model_xgb():
    """
    Trains an XGBoost model to predict the probability of a dismissal.
    This model is the responsibility of the Bowler Prediction Team.
    """
    print(" BOWLING TEAM (XGBoost) SCRIPT ".center(60, "="))

    # --- 1. Load Data ---
    print(f"🔹 Loading dataset from '{DATASET_PATH}'...")
    os.makedirs(MODELS_DIR, exist_ok=True)
    try:
        df = pd.read_csv(DATASET_PATH)
    except FileNotFoundError:
        print(f"❌ ERROR: Dataset not found. Please ensure '{DATASET_PATH}' is correct relative to your script location.")
        return

    # --- 2. Define Features and Target ---
    # KEY: We do NOT use 'total_balls' to predict dismissals.
    feature_columns = ['batsman', 'bowler', 'batting_hand', 'bowling_style', 'venue']
    target_column = 'is_dismissed' # Using a binary target
    
    # Create the binary target column
    df[target_column] = (df['dismissals'] > 0).astype(int)
    
    X = df[feature_columns]
    y = df[target_column]
    print("✅ Features and target defined for predicting dismissals.")

    # --- 3. Split Data ---
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print("🔹 Data split into training (80%) and testing (20%) sets.")

    # --- 4. Train XGBoost Classifier Model ---
    print(f"☑️  Training XGBClassifier for '{target_column}'...")
    # ✅ CLEANUP: Removed the unnecessary 'use_label_encoder' parameter
    model = XGBClassifier(objective='binary:logistic', eval_metric='logloss', random_state=42)
    model.fit(X_train, y_train)

    # --- 5. Evaluate and Save the Model ---
    preds = model.predict(X_test)
    pred_proba = model.predict_proba(X_test)[:, 1]
    print(f"   - Evaluation (Accuracy): {accuracy_score(y_test, preds):.2f}")
    print(f"   - Evaluation (AUC Score): {roc_auc_score(y_test, pred_proba):.2f}")

    joblib.dump(model, MODEL_FILENAME)
    print(f"✅ Model saved successfully to '{MODEL_FILENAME}'")
    print("=" * 60)

if __name__ == '__main__':
    train_bowler_model_xgb()

