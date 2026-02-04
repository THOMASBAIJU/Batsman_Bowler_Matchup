import os
import json
import pandas as pd
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Config
JSON_DIR = r"d:\Batsman_bowler_matchup\data_cleaning\ipl last 5 season"
OUTPUT_CSV = r"d:\Batsman_bowler_matchup\training\ball_by_ball_dataset.csv"

def get_outcome(delivery):
    """
    Determines the outcome of a delivery: 'W', '6', '4', '1', '0', etc.
    """
    # Check for Wicket
    if 'wickets' in delivery and len(delivery['wickets']) > 0:
        return 'W'
    
    # Check for Runs off Bat
    runs = delivery.get('runs', {}).get('batter', 0)
    
    if runs == 6:
        return '6'
    elif runs == 4:
        return '4'
    elif runs == 0:
        # Check if there were extras that made it not a dot ball?
        # For simplicity in "next ball outcome", usually fans care about the main event.
        # If it's a wide, it's technically an extra run, but let's classify 0 runs off bat as 0 for now
        # unless it's an extra. 
        # Detailed: 
        total_runs = delivery.get('runs', {}).get('total', 0)
        if total_runs == 0:
            return '0'
        else:
            return '1' # Treat extras/singles as '1' class bucket or keep granular? 
            # Let's keep strict runs for now.
            return '0' 
    elif runs == 1:
        return '1'
    elif runs == 2:
        return '2'
    elif runs == 3:
        return '3'
    elif runs == 5:
        return '5' # Rare but possible
    
    return '0' # Default fallback

def process_json_files():
    data = []
    
    if not os.path.exists(JSON_DIR):
        logging.error(f"Directory not found: {JSON_DIR}")
        return

    files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    logging.info(f"Found {len(files)} JSON files.")

    for filename in files:
        filepath = os.path.join(JSON_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                match = json.load(f)
                
            venue = match['info'].get('venue', 'Unknown')
            
            for innings in match.get('innings', []):
                for over in innings.get('overs', []):
                    for delivery in over.get('deliveries', []):
                        batsman = delivery['batter']
                        bowler = delivery['bowler']
                        outcome = get_outcome(delivery)
                        
                        data.append({
                            'batsman': batsman,
                            'bowler': bowler,
                            'venue': venue,
                            'outcome': outcome
                        })
                        
        except Exception as e:
            logging.warning(f"Failed to process {filename}: {e}")

    # Create DataFrame
    df = pd.DataFrame(data)
    logging.info(f"Extracted {len(df)} ball-by-ball records.")
    
    # Save to CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    logging.info(f"Saved dataset to {OUTPUT_CSV}")

if __name__ == "__main__":
    process_json_files()
