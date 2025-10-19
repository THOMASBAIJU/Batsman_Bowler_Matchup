import os
import logging
import joblib
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify
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
batting_style_to_encoding = {}
bowling_style_to_encoding = {}
df_main = pd.DataFrame()

try:
    df_batsman_map = pd.read_csv(BATSMAN_MAP_PATH)
    df_bowler_map = pd.read_csv(BOWLER_MAP_PATH)
    df_venue_map = pd.read_csv(VENUE_MAP_PATH)
    df_batting_hand_map = pd.read_csv(BATTING_HAND_MAP_PATH)
    df_bowling_style_map = pd.read_csv(BOWLING_STYLE_MAP_PATH)

    name_to_encoding['batsman'] = dict(zip(df_batsman_map['Original_Value'], df_batsman_map['Encoded_Value']))
    name_to_encoding['bowler'] = dict(zip(df_bowler_map['Original_Value'], df_bowler_map['Encoded_Value']))
    name_to_encoding['venue'] = dict(zip(df_venue_map['Original_Value'], df_venue_map['Encoded_Value']))
    
    batting_style_to_encoding = dict(zip(df_batting_hand_map['Original_Value'], df_batting_hand_map['Encoded_Value']))
    bowling_style_to_encoding = dict(zip(df_bowling_style_map['Original_Value'], df_bowling_style_map['Encoded_Value']))

    encoding_to_name['batsman'] = dict(zip(df_batsman_map['Encoded_Value'], df_batsman_map['Original_Value']))
    encoding_to_name['bowler'] = dict(zip(df_bowler_map['Encoded_Value'], df_bowler_map['Original_Value']))
    encoding_to_name['venue'] = dict(zip(df_venue_map['Encoded_Value'], df_venue_map['Original_Value']))

    df_main = pd.read_csv(DATA_PATH)
    batsman_list = sorted(df_batsman_map['Original_Value'].unique().tolist())
    bowler_list = sorted(df_bowler_map['Original_Value'].unique().tolist())
    all_players_list = sorted(list(set(batsman_list + bowler_list)))
    
    grouped = df_main.groupby(['batsman', 'bowler'])['venue'].unique().apply(list).reset_index()
    grouped['batsman_name'] = grouped['batsman'].map(encoding_to_name['batsman'])
    grouped['bowler_name'] = grouped['bowler'].map(encoding_to_name['bowler'])
    grouped['venue_names'] = grouped['venue'].apply(lambda venues: sorted([encoding_to_name['venue'].get(v) for v in venues if v is not None]))

    for record in grouped.to_dict('records'):
        batsman, bowler, venues = record['batsman_name'], record['bowler_name'], record['venue_names']
        if batsman and bowler:
            if batsman not in matchups: matchups[batsman] = {}
            matchups[batsman][bowler] = venues
    
    logging.info("✅ Successfully created all data mappings.")

except Exception as e:
    logging.error(f"An error occurred during data loading: {e}", exc_info=True)


# ---------------------------------------------------
# Load Models
# ---------------------------------------------------
models = {
    'runs': {},
    'dismissals': {}
}
model_files = {
    'runs': {
        'xgb': 'xgb_model_total_runs.joblib',
        'rf': 'rf_model_total_runs.joblib'
    },
    'dismissals': {
        'xgb': 'xgb_model_dismissals.joblib',
        'rf': 'rf_model_dismissals.joblib'
    }
}
for model_type, type_files in model_files.items():
    for algo, filename in type_files.items():
        path = os.path.join(MODELS_DIR, filename)
        try:
            models[model_type][algo] = joblib.load(path)
            logging.info(f"Loaded model: {path}")
        except FileNotFoundError:
            logging.warning(f"Model file not found: {path}")
            models[model_type][algo] = None


# ---------------------------------------------------
# Helper Function to Get Player Details from DB
# ---------------------------------------------------
def get_player_details_from_db(player_name):
    """Fetches a player's details from the SQLite database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT batting_hand, bowling_style FROM players WHERE player_name = ?", (player_name,))
        player_data = cursor.fetchone()
        conn.close()
        return dict(player_data) if player_data else {}
    except Exception as e:
        logging.error(f"DB Error for {player_name}: {e}")
        return {}


# ---------------------------------------------------
# Routes
# ---------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analysis")
def analysis():
    return render_template("analysis.html", batsman_list=batsman_list)

@app.route("/profiles")
def profiles():
    return render_template("profiles.html", all_players_list=all_players_list)

# ---------------------------------------------------
# Prediction Logic
# ---------------------------------------------------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.form
        logging.info(f"Received form data: {data}")

        batsman = data.get("batsman")
        bowler = data.get("bowler")
        venue = data.get("venue")
        
        balls_faced = int(data.get("total_balls", 0))
        
        runs_model_type = data.get("runs_model_type", "xgb")
        dismissals_model_type = data.get("dismissals_model_type", "xgb")
        
        if not all([batsman, bowler, venue]) or balls_faced <= 0:
            return jsonify({"error": "Invalid input. Please fill all fields."}), 400

        runs_model = models['runs'].get(runs_model_type)
        dismissals_model = models['dismissals'].get(dismissals_model_type)

        if not runs_model or not dismissals_model:
            return jsonify({"error": f"Model type '{runs_model_type}' or '{dismissals_model_type}' not loaded."}), 500

        # --- Feature Preparation ---
        batsman_details = get_player_details_from_db(batsman)
        bowler_details = get_player_details_from_db(bowler)

        batsman_encoded = name_to_encoding['batsman'].get(batsman)
        bowler_encoded = name_to_encoding['bowler'].get(bowler)
        venue_encoded = name_to_encoding['venue'].get(venue)
        
        batting_hand_str = batsman_details.get('batting_hand', 'N/A')
        batting_hand_encoded = batting_style_to_encoding.get(batting_hand_str)

        bowling_style_str = bowler_details.get('bowling_style', 'N/A')
        bowling_style_encoded = bowling_style_to_encoding.get(bowling_style_str)

        if any(v is None for v in [batsman_encoded, bowler_encoded, venue_encoded, batting_hand_encoded, bowling_style_encoded]):
            missing = [k for k,v in {'batsman':batsman_encoded, 'bowler':bowler_encoded, 'venue':venue_encoded, 'batting_hand':batting_hand_encoded, 'bowling_style':bowling_style_encoded}.items() if v is None]
            return jsonify({"error": f"Could not find encoded values for: {', '.join(missing)}"}), 400
        
        runs_features = np.array([[
            batsman_encoded,
            bowler_encoded,
            batting_hand_encoded,
            bowling_style_encoded,
            venue_encoded,
            balls_faced
        ]], dtype=np.float32)
        
        dismissals_features = np.array([[
            batsman_encoded,
            bowler_encoded,
            batting_hand_encoded,
            bowling_style_encoded,
            venue_encoded
        ]], dtype=np.float32)
        
        # --- Prediction ---
        predicted_runs = runs_model.predict(runs_features)[0]
        predicted_strike_rate = (predicted_runs / balls_faced) * 100 if balls_faced > 0 else 0
        dismissal_prob_value = dismissals_model.predict_proba(dismissals_features)[0][1]

        return jsonify({
            "predicted_runs": round(float(max(0, predicted_runs))),
            "strike_rate": round(float(max(0, predicted_strike_rate)), 2),
            "dismissal_prob": "Yes" if dismissal_prob_value > 0.5 else "No",
            "dismissal_rate": round(float(dismissal_prob_value), 2)
        })

    except Exception as e:
        logging.error(f"Prediction error: {e}", exc_info=True)
        return jsonify({"error": "An unexpected server error occurred."}), 500


# --- API ENDPOINTS ---
@app.route("/get_all_player_roles")
def get_all_player_roles():
    """ ✅ NEW: Fetches all players and their roles from the DB for frontend filtering. """
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT player_name, role FROM players")
        players = cursor.fetchall()
        conn.close()
        # Convert list of rows to a dictionary of {name: role}
        player_roles = {p['player_name']: p['role'] for p in players}
        return jsonify(player_roles)
    except Exception as e:
        logging.error(f"Database error in get_all_player_roles: {e}")
        return jsonify({"error": "Database error"}), 500

@app.route("/get_player_card/<player_name>")
def get_player_card(player_name):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players WHERE player_name = ?", (player_name,))
        player_data = cursor.fetchone()
        conn.close()
        if player_data:
            return jsonify(dict(player_data))
        return jsonify({"error": "Player not found"}), 404
    except Exception as e:
        logging.error(f"Database error for player {player_name}: {e}")
        return jsonify({"error": "Database error"}), 500

@app.route("/get_player_stats/<player_name>")
def get_player_stats(player_name):
    """Calculates and returns overall statistics for a given player."""
    try:
        stats = {}
        
        # Batting Stats
        batsman_encoded = name_to_encoding['batsman'].get(player_name)
        if batsman_encoded is not None:
            batting_df = df_main[df_main['batsman'] == batsman_encoded]
            if not batting_df.empty:
                total_runs = int(batting_df['total_runs'].sum())
                total_balls_faced = int(batting_df['total_balls'].sum())
                total_dismissals = int(batting_df['dismissals'].sum())
                stats['batting'] = {
                    "total_runs": total_runs, "total_balls_faced": total_balls_faced,
                    "total_dismissals": total_dismissals,
                    "strike_rate": round((total_runs / total_balls_faced) * 100, 2) if total_balls_faced > 0 else 0,
                    "average": round(total_runs / total_dismissals, 2) if total_dismissals > 0 else float(total_runs)
                }
                
                # ✅ FIX: Correctly map encoded styles back to names for chart data
                perf_vs_bowling = batting_df.groupby('bowling_style').agg(runs=('total_runs', 'sum')).reset_index()
                inv_bowling_map = {v: k for k, v in bowling_style_to_encoding.items()}
                perf_vs_bowling['bowling_style_str'] = perf_vs_bowling['bowling_style'].map(inv_bowling_map)
                stats['batting']['perf_vs_bowling_style'] = perf_vs_bowling.to_dict('records')

        # Bowling Stats
        bowler_encoded = name_to_encoding['bowler'].get(player_name)
        if bowler_encoded is not None:
            bowling_df = df_main[df_main['bowler'] == bowler_encoded]
            if not bowling_df.empty:
                total_runs_conceded = int(bowling_df['total_runs'].sum())
                total_balls_bowled = int(bowling_df['total_balls'].sum())
                total_wickets = int(bowling_df['dismissals'].sum())
                stats['bowling'] = {
                    "total_runs_conceded": total_runs_conceded, "total_balls_bowled": total_balls_bowled,
                    "total_wickets": total_wickets,
                    "economy_rate": round((total_runs_conceded / total_balls_bowled) * 6, 2) if total_balls_bowled > 0 else 0,
                    "bowling_average": round(total_runs_conceded / total_wickets, 2) if total_wickets > 0 else float(total_runs_conceded)
                }
                
                # ✅ FIX: Correctly map encoded styles back to names for chart data
                perf_vs_batting = bowling_df.groupby('batting_hand').agg(wickets=('dismissals', 'sum')).reset_index()
                inv_batting_map = {v: k for k, v in batting_style_to_encoding.items()}
                perf_vs_batting['batting_hand_str'] = perf_vs_batting['batting_hand'].map(inv_batting_map)
                stats['bowling']['perf_vs_batting_hand'] = perf_vs_batting.to_dict('records')

        if not stats:
            return jsonify({"error": "Player has no stats in this dataset."}), 404
        return jsonify(stats)

    except Exception as e:
        logging.error(f"Error getting stats for {player_name}: {e}", exc_info=True)
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

