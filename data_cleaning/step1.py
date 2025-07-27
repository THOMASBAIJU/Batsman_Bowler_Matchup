import pandas as pd
import json
import os
import glob 


def process_single_match_data(match_json_data):
    """
    Extrac`ts delivery-level data (batter, bowler, runs, wickets) from a single match's JSON.
    Returns a list of dictionaries, each representing a delivery.
    """
    deliveries_list = []
    # Safely access 'innings' key, returning an empty list if not found
    for inning in match_json_data.get('innings', []):
        # Safely access 'overs' key
        for over_data in inning.get('overs', []):
            # Safely access 'deliveries' key
            for delivery in over_data.get('deliveries', []):
                batter = delivery.get('batter')
                bowler = delivery.get('bowler')

                # Get runs information safely
                runs_info = delivery.get('runs', {})
                runs_batter = runs_info.get('batter', 0)
                runs_extras = runs_info.get('extras', 0)
                total_runs_on_delivery = runs_info.get('total', 0) # total runs off this specific ball

                # Check if a wicket fell on this delivery
                is_wicket = 1 if delivery.get('wickets') else 0

                # Only include valid deliveries where batter and bowler are identified
                if batter and bowler:
                    deliveries_list.append({
                        'batter': batter,
                        'bowler': bowler,
                        'runs_batter': runs_batter,          # Runs scored by the batter
                        'runs_extras': runs_extras,          # Runs from extras (wides, no-balls, byes, leg-byes)
                        'total_runs_on_delivery': total_runs_on_delivery, # Total runs added to score (batter + extras)
                        'is_wicket': is_wicket               # 1 if wicket, 0 otherwise
                    })
    return deliveries_list

def create_batsman_bowler_matchup_csv(json_files_directory, output_csv_filename='all_matches_batsman_bowler_matchup.csv'):
    """
    Processes multiple JSON match files to create a single CSV with aggregated
    batsman-bowler matchup statistics, including strike rate and dismissal rate.

    Args:
        json_files_directory (str): The path to the directory containing your JSON match files.
        output_csv_filename (str): The name for the output CSV file.
    """
    all_deliveries_combined = []

    # Get all JSON files in the specified directory
    json_file_paths = glob.glob(os.path.join(json_files_directory, '*.json'))

    if not json_file_paths:
        print(f"No JSON files found in the directory: {json_files_directory}")
        print("Please ensure the path is correct and files have a .json extension.")
        return

    print(f"Found {len(json_file_paths)} JSON files to process.")

    for i, file_path in enumerate(json_file_paths):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                match_json_data = json.load(f)

            # Process data from the current match and extend the combined list
            all_deliveries_combined.extend(process_single_match_data(match_json_data))
            if (i + 1) % 50 == 0 or (i + 1) == len(json_file_paths):
                print(f"Processed {i + 1}/{len(json_file_paths)} files.")

        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from file: {file_path}. Skipping this file.")
        except Exception as e:
            print(f"An unexpected error occurred while processing {file_path}: {e}. Skipping this file.")

    if not all_deliveries_combined:
        print("No delivery data was successfully extracted from any file. CSV will not be created.")
        return

    # Create a single DataFrame from all collected deliveries
    full_deliveries_df = pd.DataFrame(all_deliveries_combined)

    # Aggregate data by 'batter' and 'bowler' across all matches
    batsman_bowler_matchup_agg = full_deliveries_df.groupby(['batter', 'bowler']).agg(
        balls_faced=('batter', 'size'),               # Count of deliveries faced
        runs_scored_by_batter=('runs_batter', 'sum'), # Sum of runs scored directly by the batter
        total_runs_off_ball=('total_runs_on_delivery', 'sum'), # Sum of total runs off the bat including extras
        wickets_taken=('is_wicket', 'sum')            # Sum of wickets taken
    ).reset_index()

    # Calculate Strike Rate: (Runs Scored by Batter / Balls Faced) * 100
    # Handle division by zero for balls_faced
    batsman_bowler_matchup_agg['strike_rate'] = batsman_bowler_matchup_agg.apply(
        lambda row: (row['runs_scored_by_batter'] / row['balls_faced']) * 100 if row['balls_faced'] > 0 else 0,
        axis=1
    )

    # Calculate Dismissal Rate: (Wickets Taken / Balls Faced) * 100
    # Handle division by zero for balls_faced
    batsman_bowler_matchup_agg['dismissal_rate'] = batsman_bowler_matchup_agg.apply(
        lambda row: (row['wickets_taken'] / row['balls_faced']) * 100 if row['balls_faced'] > 0 else 0,
        axis=1
    )


    # Rename columns for better readability in the CSV
    batsman_bowler_matchup_agg.rename(columns={
        'batter': 'Batter',
        'bowler': 'Bowler',
        'balls_faced': 'Balls Faced',
        'runs_scored_by_batter': 'Runs Scored (Batter)',
        'total_runs_off_ball': 'Total Runs (Incl. Extras)',
        'wickets_taken': 'Wickets Taken',
        'strike_rate': 'Strike Rate',
        'dismissal_rate': 'Dismissal Rate'
    }, inplace=True)

    # Save the aggregated DataFrame to a CSV file
    try:
        batsman_bowler_matchup_agg.to_csv(output_csv_filename, index=False, encoding='utf-8')
        print(f"\nSuccessfully created aggregated CSV file: '{output_csv_filename}'")
    except Exception as e:
        print(f"Error saving CSV file: {e}")

# --- How to use the script ---
if __name__ == "__main__":
    # IMPORTANT: Replace 'path/to/your/json_files' with the actual path to your folder
    # For example, if your files are in C:\CricketData\IPL2021\Matches or /Users/YourUser/CricketData/IPL2021/Matches
    your_json_data_directory = 'D:\Mini Project\ipl last 5 season' # <--- CHANGE THIS LINE

    # You can specify a different output filename if you wish
    output_filename = 'all_ipl_batsman_bowler_stats.csv'

    create_batsman_bowler_matchup_csv(your_json_data_directory, output_filename)