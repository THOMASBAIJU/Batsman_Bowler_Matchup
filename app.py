import os
import logging
import joblib
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, flash, jsonify
from xgboost import XGBClassifier, XGBRegressor

# ---------------------------------------------------
# Flask App Config
# ---------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_change_this'
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------
# Define File Paths
# ---------------------------------------------------
DATA_PATH = r"D:\Batsman_bowler_matchup\data_cleaning\final\final_dataset.csv"
MAPS_DIR = "maps"
MODELS_DIR = "models"

BATSMAN_MAP_PATH = os.path.join(MAPS_DIR, "batsman_encoding_map.csv")
BOWLER_MAP_PATH = os.path.join(MAPS_DIR, "bowler_encoding_map.csv")
VENUE_MAP_PATH = os.path.join(MAPS_DIR, "venue_encoding_map.csv")

# ---------------------------------------------------
# Load Data & Create Mappings at Startup
# ---------------------------------------------------
matchups = {}
batsman_list = []
name_to_encoding = {}
batsman_hand_map = {}
bowler_style_map = {}
df_main = pd.DataFrame()

try:
    # --- Step 1: Load the mapping files to get the names ---
    df_batsman_map = pd.read_csv(BATSMAN_MAP_PATH)
    df_bowler_map = pd.read_csv(BOWLER_MAP_PATH)
    df_venue_map = pd.read_csv(VENUE_MAP_PATH)

    # Convert values to string to prevent data type errors
    for df_map in [df_batsman_map, df_bowler_map, df_venue_map]:
        df_map['Original_Value'] = df_map['Original_Value'].astype(str)
        df_map['Encoded_Value'] = df_map['Encoded_Value']

    # Create dictionaries to map names to their encoded values for the model
    name_to_encoding['batsman'] = dict(zip(df_batsman_map['Original_Value'], df_batsman_map['Encoded_Value']))
    name_to_encoding['bowler'] = dict(zip(df_bowler_map['Original_Value'], df_bowler_map['Encoded_Value']))
    name_to_encoding['venue'] = dict(zip(df_venue_map['Original_Value'], df_venue_map['Encoded_Value']))

    encoding_to_name = {
        'batsman': dict(zip(df_batsman_map['Encoded_Value'], df_batsman_map['Original_Value'])),
        'bowler': dict(zip(df_bowler_map['Encoded_Value'], df_bowler_map['Original_Value'])),
        'venue': dict(zip(df_venue_map['Encoded_Value'], df_venue_map['Original_Value']))
    }
    logging.info("Successfully loaded all encoding map files.")

    # --- Step 2: Load the main dataset ---
    df_main = pd.read_csv(DATA_PATH)

    # --- Step 3: Combine maps with the main dataset to get names ---
    df_main['batsman_name'] = df_main['batsman'].map(encoding_to_name['batsman'])
    df_main['bowler_name'] = df_main['bowler'].map(encoding_to_name['bowler'])
    df_main['venue_name'] = df_main['venue'].map(encoding_to_name['venue'])
    df_main.dropna(subset=['batsman_name', 'bowler_name', 'venue_name'], inplace=True)
    
    # --- Step 4: Build the matchup dictionary using names ---
    batsman_list = sorted(df_main['batsman_name'].unique().tolist())
    grouped = df_main.groupby(['batsman_name', 'bowler_name'])['venue_name'].unique().apply(list).reset_index()
    for record in grouped.to_dict('records'):
        batsman = record['batsman_name']
        bowler = record['bowler_name']
        venues = record['venue_name']
        if batsman not in matchups:
            matchups[batsman] = {}
        matchups[batsman][bowler] = sorted(venues)
    logging.info("Successfully created matchup dictionary.")

    # --- Step 5: Create maps for batting hand and bowling style ---
    if 'batting_hand' in df_main.columns:
        batsman_hand_map = df_main.drop_duplicates(subset=['batsman_name']).set_index('batsman_name')['batting_hand'].to_dict()
    if 'bowling_style' in df_main.columns:
        bowler_style_map = df_main.drop_duplicates(subset=['bowler_name']).set_index('bowler_name')['bowling_style'].to_dict()
    logging.info("Successfully created batting hand and bowling style maps.")

except FileNotFoundError as e:
    logging.error(f"FATAL: Could not find a required file: {e}.")
except Exception as e:
    logging.error(f"An error occurred during data loading: {e}", exc_info=True)

# ---------------------------------------------------
# Load Models
# ---------------------------------------------------
models = {}
model_files = {
    "total_runs": "xgb_model_total_runs.joblib",
    "dismissals": "xgb_model_dismissals.joblib",
    "dismissal_rate": "xgb_model_dismissal_rate.joblib",
    "strike_rate": "xgb_model_strike_rate.joblib",
}

for key, filename in model_files.items():
    path = os.path.join(MODELS_DIR, filename)
    try:
        models[key] = joblib.load(path)
        logging.info(f"Loaded model: {path} (Type: {type(models[key])})")
    except FileNotFoundError:
        logging.warning(f"Model file not found: {path}")

# ---------------------------------------------------
# Prediction Logic
# ---------------------------------------------------
def predict_outcomes(batsman_name, bowler_name, venue_name, balls_faced):
    try:
        batsman_enc = name_to_encoding['batsman'].get(batsman_name)
        bowler_enc = name_to_encoding['bowler'].get(bowler_name)
        venue_enc = name_to_encoding['venue'].get(venue_name)
        batting_hand_enc = batsman_hand_map.get(batsman_name)
        bowling_style_enc = bowler_style_map.get(bowler_name)

        if None in [batsman_enc, bowler_enc, venue_enc, batting_hand_enc, bowling_style_enc]:
            flash("Could not find required encoded value for prediction.")
            return None

        # The feature array now directly uses the 'balls_faced' value from the UI
        features = np.array([[
            batsman_enc,
            bowler_enc,
            balls_faced, # Using the user's input as a direct feature
            batting_hand_enc,
            bowling_style_enc,
            venue_enc
        ]])
        
        results = {}
        
        if "total_runs" in models:
            predicted_runs_per_ball = models["total_runs"].predict(features)[0]
            predicted_total_runs = predicted_runs_per_ball * balls_faced
            results["predicted_runs"] = round(float(predicted_total_runs), 2)
        
        if "dismissals" in models:
            dismissal_model = models["dismissals"]
            if isinstance(dismissal_model, XGBClassifier):
                probability = dismissal_model.predict_proba(features)[0][1]
                results["dismissal_prob"] = "Yes" if probability >= 0.5 else "No"
            else: # Fallback for regressor
                prediction = dismissal_model.predict(features)[0]
                results["dismissal_prob"] = "Yes" if prediction >= 0.5 else "No"

        if "dismissal_rate" in models:
            results["dismissal_rate"] = round(float(models["dismissal_rate"].predict(features)[0]), 3)
        
        if "strike_rate" in models:
            results["strike_rate"] = round(float(models["strike_rate"].predict(features)[0]), 2)
            
        return results
    except Exception as e:
        logging.error(f"Prediction error: {e}", exc_info=True)
        flash("An error occurred during prediction.")
        return None

# ---------------------------------------------------
# Routes
# ---------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html", batsman_list=batsman_list)

@app.route("/predict", methods=["POST"])
def predict():
    batsman = request.form.get("batsman")
    bowler = request.form.get("bowler")
    venue = request.form.get("venue")
    balls_faced_str = request.form.get("balls")
    
    try:
        balls_faced = int(balls_faced_str) if balls_faced_str and balls_faced_str.isdigit() else 0
    except (ValueError, TypeError):
        flash("Invalid value for Balls Faced. Using 0.")
        balls_faced = 0
    
    predictions = predict_outcomes(batsman, bowler, venue, balls_faced)
    
    if predictions:
        return jsonify(predictions)
    else:
        return jsonify({"error": "Prediction failed. Check server logs."}), 500

# --- API ENDPOINTS FOR DYNAMIC DROPDOWNS ---
@app.route("/get_bowlers/<batsman_name>")
def get_bowlers(batsman_name):
    if batsman_name in matchups:
        return jsonify(sorted(list(matchups[batsman_name].keys())))
    return jsonify([])

@app.route("/get_venues/<batsman_name>/<bowler_name>")
def get_venues(batsman_name, bowler_name):
    if batsman_name in matchups and bowler_name in matchups.get(batsman_name, {}):
        return jsonify(matchups[batsman_name][bowler_name])
    return jsonify([])
    
# ---------------------------------------------------
# Run App
# ---------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")

