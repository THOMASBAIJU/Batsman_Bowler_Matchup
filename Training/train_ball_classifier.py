import pandas as pd
import joblib
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import os
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Paths
DATA_PATH = r"d:\Batsman_bowler_matchup\training\ball_by_ball_dataset.csv"
MAPS_DIR = r"d:\Batsman_bowler_matchup\maps"
MODELS_DIR = r"d:\Batsman_bowler_matchup\models"

def main():
    # 1. Load Data
    if not os.path.exists(DATA_PATH):
        logging.error(f"Dataset not found: {DATA_PATH}")
        return
    
    df = pd.read_csv(DATA_PATH)
    logging.info(f"Loaded dataset with {len(df)} records.")
    
    # 2. Load Encoding Maps
    try:
        batsman_map = pd.read_csv(os.path.join(MAPS_DIR, "batsman_encoding_map.csv")).set_index('Original_Value')['Encoded_Value'].to_dict()
        bowler_map = pd.read_csv(os.path.join(MAPS_DIR, "bowler_encoding_map.csv")).set_index('Original_Value')['Encoded_Value'].to_dict()
        venue_map = pd.read_csv(os.path.join(MAPS_DIR, "venue_encoding_map.csv")).set_index('Original_Value')['Encoded_Value'].to_dict()
    except Exception as e:
        logging.error(f"Failed to load encoding maps: {e}")
        return

    # 3. Encode Features
    # We map the names to IDs. If a name is missing, we drop the row (or could handle as unknown).
    # For high quality model, dropping unknown is safer.
    
    df['batsman_encoded'] = df['batsman'].map(batsman_map)
    df['bowler_encoded'] = df['bowler'].map(bowler_map)
    df['venue_encoded'] = df['venue'].map(venue_map)
    
    # Drop rows with missing encodings
    original_len = len(df)
    df.dropna(subset=['batsman_encoded', 'bowler_encoded', 'venue_encoded'], inplace=True)
    logging.info(f"Dropped {original_len - len(df)} rows due to missing entity mappings.")
    
    if len(df) == 0:
        logging.error("No data left after mapping! Check if maps match the dataset names.")
        return

    # 4. Prepare Target (Outcome)
    le = LabelEncoder()
    df['outcome_encoded'] = le.fit_transform(df['outcome'])
    logging.info(f"Target Classes: {le.classes_}")
    
    # 5. Train/Test Split
    X = df[['batsman_encoded', 'bowler_encoded', 'venue_encoded']]
    y = df['outcome_encoded']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 6. Train Model
    logging.info("Training XGBClassifier...")
    model = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        objective='multi:softprob', 
        num_class=len(le.classes_),
        eval_metric='mlogloss'
    )
    model.fit(X_train, y_train)
    
    # 7. Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    logging.info(f"Model Accuracy: {acc:.4f}")
    logging.info("\n" + classification_report(y_test, y_pred, target_names=[str(c) for c in le.classes_]))
    
    # 8. Save Model & Encoder
    os.makedirs(MODELS_DIR, exist_ok=True)
    joblib.dump(model, os.path.join(MODELS_DIR, "xgb_ball_outcome.joblib"))
    joblib.dump(le, os.path.join(MODELS_DIR, "outcome_encoder.joblib"))
    logging.info("Saved model and encoder to 'models/' directory.")

if __name__ == "__main__":
    main()