import pandas as pd
import sqlite3
import os

# --- Configuration ---
DATASET_PATH = r"D:\Batsman_bowler_matchup\data_cleaning\final\final_dataset.csv"
DB_FILE = "players.db"
MAPS_DIR = "maps"
BATSMAN_MAP_PATH = os.path.join(MAPS_DIR, "batsman_encoding_map.csv")
BOWLER_MAP_PATH = os.path.join(MAPS_DIR, "bowler_encoding_map.csv")
BATTING_HAND_MAP_PATH = os.path.join(MAPS_DIR, "batting_hand_encoding_map.csv")
BOWLING_STYLE_MAP_PATH = os.path.join(MAPS_DIR, "bowling_style_encoding_map.csv")


def create_database():
    """
    Creates a fresh SQLite database, intelligently merging batsman and bowler data
    to create complete profiles for all players, including all-rounders.
    """
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"✅ Removed old database file: {DB_FILE}")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    print(f"✅ Database '{DB_FILE}' created successfully.")

    cursor.execute('''
        CREATE TABLE players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL UNIQUE,
            role TEXT,
            batting_hand TEXT,
            bowling_style TEXT,
            profile_image_url TEXT
        );
    ''')
    print("✅ Table 'players' created successfully.")

    try:
        df = pd.read_csv(DATASET_PATH)
        
        # Load all necessary encoding maps
        df_batsman_map = pd.read_csv(BATSMAN_MAP_PATH)
        df_bowler_map = pd.read_csv(BOWLER_MAP_PATH)
        df_batting_hand_map = pd.read_csv(BATTING_HAND_MAP_PATH)
        df_bowling_style_map = pd.read_csv(BOWLING_STYLE_MAP_PATH)

        # Create dictionaries to decode numbers back to text
        encoding_to_name = {
            'batsman': dict(zip(df_batsman_map['Encoded_Value'], df_batsman_map['Original_Value'])),
            'bowler': dict(zip(df_bowler_map['Encoded_Value'], df_bowler_map['Original_Value'])),
            'batting_hand': dict(zip(df_batting_hand_map['Encoded_Value'], df_batting_hand_map['Original_Value'])),
            'bowling_style': dict(zip(df_bowling_style_map['Encoded_Value'], df_bowling_style_map['Original_Value']))
        }
        
        # Decode all relevant columns to get original text values
        df['batsman_name'] = df['batsman'].map(encoding_to_name['batsman'])
        df['bowler_name'] = df['bowler'].map(encoding_to_name['bowler'])
        df['batting_hand_str'] = df['batting_hand'].map(encoding_to_name['batting_hand'])
        df['bowling_style_str'] = df['bowling_style'].map(encoding_to_name['bowling_style'])

        df.dropna(subset=['batsman_name', 'bowler_name'], inplace=True)

        # MODIFIED: Logic to correctly handle all-rounders
        # 1. Get unique data for batsmen and bowlers separately
        batsmen_info = df[['batsman_name', 'batting_hand_str']].drop_duplicates('batsman_name').rename(columns={'batsman_name': 'player_name', 'batting_hand_str': 'batting_hand'})
        bowlers_info = df[['bowler_name', 'bowling_style_str']].drop_duplicates('bowler_name').rename(columns={'bowler_name': 'player_name', 'bowling_style_str': 'bowling_style'})

        # 2. Merge the two dataframes using an outer join. This combines rows for all-rounders.
        all_players = pd.merge(batsmen_info, bowlers_info, on='player_name', how='outer')

        print(f"ℹ️  Found {len(all_players)} unique players. Inserting into database...")
        for _, row in all_players.iterrows():
            player_name = str(row['player_name'])
            
            # Get batting and bowling styles, filling missing values with 'N/A'
            batting_hand = row.get('batting_hand', 'N/A')
            if pd.isna(batting_hand): batting_hand = 'N/A'
            
            bowling_style = row.get('bowling_style', 'N/A')
            if pd.isna(bowling_style): bowling_style = 'N/A'

            # Determine a primary role for display, though the frontend will handle context
            role = 'Unknown'
            is_batsman = batting_hand != 'N/A'
            is_bowler = bowling_style != 'N/A'
            if is_batsman and is_bowler:
                role = 'All-Rounder'
            elif is_batsman:
                role = 'Batsman'
            elif is_bowler:
                role = 'Bowler'
            
            image_filename = player_name.replace(' ', '_') + ".png"
            # Corrected path to match your folder structure
            profile_image_url = f"static/assets/img/Players/{image_filename}"

            cursor.execute('''
                INSERT OR IGNORE INTO players (player_name, role, batting_hand, bowling_style, profile_image_url)
                VALUES (?, ?, ?, ?, ?)
            ''', (player_name, role, batting_hand, bowling_style, profile_image_url))

        conn.commit()
        print("\n✅ Database setup complete. All players have been added.")

    except FileNotFoundError as e:
        print(f"❌ ERROR: A required mapping file was not found. Please ensure all .csv files are in the 'maps' directory. Missing file: {e.filename}")
    except Exception as e:
        print(f"❌ An error occurred during database setup: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()

