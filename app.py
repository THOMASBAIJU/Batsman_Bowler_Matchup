import os
import logging
import joblib
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify
from xgboost import XGBClassifier, XGBRegressor
import sqlite3

# ---------------------------------------------------
# Flask App Config
# ---------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_super_secret_key_change_this'
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------
# Define File Paths
# ---------------------------------------------------
DB_FILE = "players.db"
# This path should be relative
DATA_PATH = "final_dataset.csv"
MAPS_DIR = "maps"
MODELS_DIR = "models"
BATSMAN_MAP_PATH = os.path.join(MAPS_DIR, "batsman_encoding_map.csv")
BOWLER_MAP_PATH = os.path.join(MAPS_DIR, "bowler_encoding_map.csv")
VENUE_MAP_PATH = os.path.join(MAPS_DIR, "venue_encoding_map.csv")
BATTING_HAND_MAP_PATH = os.path.join(MAPS_DIR, "batting_hand_encoding_map.csv")
BOWLING_STYLE_MAP_PATH = os.path.join(MAPS_DIR, "bowling_style_encoding_map.csv")


# ---------------------------------------------------
# Load Data & Create Mappings at Startup
# ---------------------------------------------------
matchups = {}
batsman_list = []
all_players_list = []
name_to_encoding = {}
encoding_to_name = {}
batsman_hand_map = {}
bowler_style_map = {}
df_main = pd.DataFrame()

try:
    # --- Step 1: Load mapping files ---
    df_batsman_map = pd.read_csv(BATSMAN_MAP_PATH)
    df_bowler_map = pd.read_csv(BOWLER_MAP_PATH)
    df_venue_map = pd.read_csv(VENUE_MAP_PATH)
    df_batting_hand_map = pd.read_csv(BATTING_HAND_MAP_PATH)
    df_bowling_style_map = pd.read_csv(BOWLING_STYLE_MAP_PATH)

    for df_map in [df_batsman_map, df_bowler_map, df_venue_map, df_batting_hand_map, df_bowling_style_map]:
        df_map['Original_Value'] = df_map['Original_Value'].astype(str)

    name_to_encoding['batsman'] = dict(zip(df_batsman_map['Original_Value'], df_batsman_map['Encoded_Value']))
    name_to_encoding['bowler'] = dict(zip(df_bowler_map['Original_Value'], df_bowler_map['Encoded_Value']))
    name_to_encoding['venue'] = dict(zip(df_venue_map['Original_Value'], df_venue_map['Encoded_Value']))
    
    encoding_to_name = {
        'batsman': dict(zip(df_batsman_map['Encoded_Value'], df_batsman_map['Original_Value'])),
        'bowler': dict(zip(df_bowler_map['Encoded_Value'], df_bowler_map['Original_Value'])),
        'venue': dict(zip(df_venue_map['Encoded_Value'], df_venue_map['Original_Value'])),
        'batting_hand': dict(zip(df_batting_hand_map['Encoded_Value'], df_batting_hand_map['Original_Value'])),
        'bowling_style': dict(zip(df_bowling_style_map['Encoded_Value'], df_bowling_style_map['Original_Value']))
    }
    logging.info("Successfully loaded all encoding map files.")

    # --- Step 2: Load and process main dataset ---
    df_main = pd.read_csv(DATA_PATH)
    df_main['batsman_name'] = df_main['batsman'].map(encoding_to_name['batsman'])
    df_main['bowler_name'] = df_main['bowler'].map(encoding_to_name['bowler'])
    df_main['venue_name'] = df_main['venue'].map(encoding_to_name['venue'])
    df_main['batting_hand_str'] = df_main['batting_hand'].map(encoding_to_name['batting_hand'])
    df_main['bowling_style_str'] = df_main['bowling_style'].map(encoding_to_name['bowling_style'])
    df_main.dropna(subset=['batsman_name', 'bowler_name', 'venue_name'], inplace=True)
    
    # --- Step 3: Build matchup and player data dictionaries ---
    batsman_list = sorted(df_main['batsman_name'].unique().tolist())
    all_players_list = sorted(list(set(batsman_list + df_main['bowler_name'].unique().tolist())))
    
    grouped = df_main.groupby(['batsman_name', 'bowler_name'])['venue_name'].unique().apply(list).reset_index()
    for record in grouped.to_dict('records'):
        batsman, bowler, venues = record['batsman_name'], record['bowler_name'], record['venue_name']
        if batsman not in matchups: matchups[batsman] = {}
        matchups[batsman][bowler] = sorted(venues)
    
    if 'batting_hand' in df_main.columns:
        batsman_hand_map = df_main.drop_duplicates(subset=['batsman_name']).set_index('batsman_name')['batting_hand'].to_dict()
    if 'bowling_style' in df_main.columns:
        bowler_style_map = df_main.drop_duplicates(subset=['bowler_name']).set_index('bowler_name')['bowling_style'].to_dict()
    logging.info("Successfully created all data mappings.")

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
        features_dict = {
            'batsman': name_to_encoding['batsman'].get(batsman_name),
            'bowler': name_to_encoding['bowler'].get(bowler_name),
            'total_balls': balls_faced,
            'batting_hand': batsman_hand_map.get(batsman_name),
            'bowling_style': bowler_style_map.get(bowler_name),
            'venue': name_to_encoding['venue'].get(venue_name)
        }
        if None in features_dict.values():
            return {"error": "Could not find required encoded value for prediction."}

        features = np.array([[
            features_dict['batsman'], features_dict['bowler'], features_dict['total_balls'],
            features_dict['batting_hand'], features_dict['bowling_style'], features_dict['venue']
        ]])
        
        results = {}
        
        if "total_runs" in models:
            # CORRECTED: The model now predicts total runs directly.
            predicted_total_runs = models["total_runs"].predict(features)[0]
            # The multiplication step has been removed.
            results["predicted_runs"] = round(float(max(0, predicted_total_runs)))
        
        if "dismissals" in models and isinstance(models["dismissals"], XGBClassifier):
            prob = models["dismissals"].predict_proba(features)[0][1]
            results["dismissal_prob"] = "Yes" if prob >= 0.5 else "No"
            
        if "dismissal_rate" in models:
            predicted_rate = models["dismissal_rate"].predict(features)[0]
            results["dismissal_rate"] = round(float(max(0, predicted_rate)), 3)
            
        if "strike_rate" in models:
            predicted_sr = models["strike_rate"].predict(features)[0]
            results["strike_rate"] = round(float(max(0, predicted_sr)), 2)
            
        return results
    except Exception as e:
        logging.error(f"Prediction error: {e}", exc_info=True)
        return {"error": "An error occurred during prediction."}


# ---------------------------------------------------
# Routes
# ---------------------------------------------------
@app.route("/")
def index():
    """Renders the main home page."""
    return render_template("index.html")

@app.route("/analysis")
def analysis():
    """Renders the analysis page where users can make predictions."""
    return render_template("analysis.html", batsman_list=batsman_list)

@app.route("/profiles")
def profiles():
    """Renders the player profile and comparison page."""
    return render_template("profiles.html", all_players_list=all_players_list)

@app.route("/predict", methods=["POST"])
def predict():
    """Handles prediction requests from the analysis page."""
    batsman = request.form.get("batsman")
    bowler = request.form.get("bowler")
    venue = request.form.get("venue")
    balls_faced_str = request.form.get("total_balls")
    
    try:
        balls_faced = int(balls_faced_str) if balls_faced_str and balls_faced_str.isdigit() else 0
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid value for Balls Faced."}), 400
    
    predictions = predict_outcomes(batsman, bowler, venue, balls_faced)
    
    if "error" in predictions:
        return jsonify(predictions), 500
    return jsonify(predictions)

# --- API ENDPOINTS ---
@app.route("/get_player_card/<player_name>")
def get_player_card(player_name):
    """
    Fetches all player details (name, role, style, image URL) from the database
    and returns them as JSON to be displayed on the player cards.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players WHERE player_name = ?", (player_name,))
        player_data = cursor.fetchone()
        conn.close()
        if player_data:
            player_dict = dict(player_data)
            logging.info(f"Returning player card data for {player_name}: {player_dict}")
            return jsonify(player_dict)
        
        logging.warning(f"Player card data not found for: {player_name}")
        return jsonify({"error": "Player not found"}), 404
    except Exception as e:
        logging.error(f"Database error for player {player_name}: {e}")
        return jsonify({"error": "Database error"}), 500

@app.route("/get_player_stats/<player_name>")
def get_player_stats(player_name):
    """Calculates and returns overall statistics for a given player."""
    try:
        stats = {}
        
        # --- Batting Stats ---
        is_batsman = player_name in df_main['batsman_name'].values
        if is_batsman:
            batting_df = df_main[df_main['batsman_name'] == player_name]
            total_runs = int(batting_df['total_runs'].sum())
            total_balls_faced = int(batting_df['total_balls'].sum())
            total_dismissals = int(batting_df['dismissals'].sum())
            
            batting_stats = {
                "total_runs": total_runs,
                "total_balls_faced": total_balls_faced,
                "total_dismissals": total_dismissals,
                "strike_rate": round((total_runs / total_balls_faced) * 100, 2) if total_balls_faced > 0 else 0,
                "average": round(total_runs / total_dismissals, 2) if total_dismissals > 0 else total_runs
            }
            stats['batting'] = batting_stats
            
            # Performance vs Bowling Type
            perf_vs_bowling = batting_df.groupby('bowling_style_str').agg(
                runs=('total_runs', 'sum'),
                balls=('total_balls', 'sum')
            ).reset_index()
            perf_vs_bowling['strike_rate'] = round((perf_vs_bowling['runs'] / perf_vs_bowling['balls']) * 100, 2)
            stats['batting']['perf_vs_bowling_style'] = perf_vs_bowling.to_dict('records')

        # --- Bowling Stats ---
        is_bowler = player_name in df_main['bowler_name'].values
        if is_bowler:
            bowling_df = df_main[df_main['bowler_name'] == player_name]
            total_runs_conceded = int(bowling_df['total_runs'].sum())
            total_balls_bowled = int(bowling_df['total_balls'].sum())
            total_wickets = int(bowling_df['dismissals'].sum())
            
            bowling_stats = {
                "total_runs_conceded": total_runs_conceded,
                "total_balls_bowled": total_balls_bowled,
                "total_wickets": total_wickets,
                "economy_rate": round((total_runs_conceded / total_balls_bowled) * 6, 2) if total_balls_bowled > 0 else 0,
                "bowling_average": round(total_runs_conceded / total_wickets, 2) if total_wickets > 0 else total_runs_conceded
            }
            stats['bowling'] = bowling_stats
            
            # Performance vs Batting Hand
            perf_vs_batting = bowling_df.groupby('batting_hand_str').agg(
                wickets=('dismissals', 'sum'),
                runs=('total_runs', 'sum')
            ).reset_index()
            stats['bowling']['perf_vs_batting_hand'] = perf_vs_batting.to_dict('records')
            
        if not stats:
            return jsonify({"error": "Player has no stats in this dataset."}), 404
            
        return jsonify(stats)

    except Exception as e:
        logging.error(f"Error getting stats for {player_name}: {e}")
        return jsonify({"error": "Could not calculate player stats."}), 500

@app.route("/get_bowlers/<batsman_name>")
def get_bowlers(batsman_name):
    return jsonify(sorted(list(matchups.get(batsman_name, {}).keys())))

@app.route("/get_venues/<batsman_name>/<bowler_name>")
def get_venues(batsman_name, bowler_name):
    return jsonify(matchups.get(batsman_name, {}).get(bowler_name, []))

# ---------------------------------------------------
# Run App
# ---------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")