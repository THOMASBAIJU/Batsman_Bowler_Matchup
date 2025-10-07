import pandas as pd
import os
import shutil
from fuzzywuzzy import process
from PIL import Image

# --- CONFIGURATION: PLEASE EDIT THESE PATHS ---
# 1. Path to your main dataset CSV file.
DATASET_PATH = r"final_dataset.csv"

# 2. Path to the parent folder containing all your player image folders (e.g., "Virat Kholi", "MS Dhoni", etc.).
IMAGE_DATASET_PATH = r"D:\path\to\your\image_folders"

# 3. Path where the script will save the final, renamed images. This should match your Flask app's static folder.
OUTPUT_IMAGE_PATH = r"D:\Batsman_bowler_matchup\static\images\players"

# 4. The target resolution for all output images (width, height) in pixels.
TARGET_RESOLUTION = (256, 256)
# ------------------------------------------------

# The minimum similarity score (out of 100) required to consider a match valid.
# Adjust this if you get too many incorrect matches (increase it) or too few matches (decrease it).
MATCH_THRESHOLD = 85

def standardize_name(name):
    """Converts a player name into a standard filename format (e.g., 'V Kholi' -> 'V_Kholi.png')."""
    return name.replace(' ', '_') + ".png"

def find_first_image(folder_path):
    """Finds the first valid image file (.png, .jpg, .jpeg) in a given folder."""
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            return os.path.join(folder_path, filename)
    return None

def resize_and_save_image(source_path, destination_path, resolution):
    """Opens an image, resizes it to a standard resolution, and saves it as a PNG."""
    try:
        with Image.open(source_path) as img:
            # Use LANCZOS for the highest quality downscaling
            resized_img = img.resize(resolution, Image.Resampling.LANCZOS)
            # Convert to RGB to avoid issues with transparency or different color modes
            if resized_img.mode != 'RGB':
                resized_img = resized_img.convert('RGB')
            # Save the result as a PNG file
            resized_img.save(destination_path, 'PNG')
        return True
    except Exception as e:
        print(f"   ❌ ERROR processing image {os.path.basename(source_path)}: {e}")
        return False

def main():
    print("--- Starting Player Image Matching and Resizing Process ---")

    # --- 1. Load Unique Player Names from the Dataset ---
    try:
        df = pd.read_csv(DATASET_PATH)
        batsman_names = set(df['batsman_name'].dropna().unique())
        bowler_names = set(df['bowler_name'].dropna().unique())
        dataset_player_names = sorted(list(batsman_names.union(bowler_names)))
        print(f"✅ Found {len(dataset_player_names)} unique player names in the dataset.")
    except FileNotFoundError:
        print(f"❌ ERROR: Dataset not found at '{DATASET_PATH}'. Please check the path.")
        return
    except KeyError:
        print("❌ ERROR: The CSV must contain 'batsman_name' and 'bowler_name' columns.")
        return

    # --- 2. Get Image Folder Names ---
    try:
        image_folder_names = [name for name in os.listdir(IMAGE_DATASET_PATH) if os.path.isdir(os.path.join(IMAGE_DATASET_PATH, name))]
        if not image_folder_names:
            print(f"❌ ERROR: No image folders found in '{IMAGE_DATASET_PATH}'. Please check the path.")
            return
        print(f"✅ Found {len(image_folder_names)} player image folders.")
    except FileNotFoundError:
        print(f"❌ ERROR: Image directory not found at '{IMAGE_DATASET_PATH}'. Please check the path.")
        return

    # --- 3. Create Output Directory ---
    os.makedirs(OUTPUT_IMAGE_PATH, exist_ok=True)
    print(f"✅ Output directory is ready at '{OUTPUT_IMAGE_PATH}'.")

    # --- 4. Match, Resize, and Save Images ---
    print("\n--- Matching names and processing images ---")
    success_count = 0
    fail_count = 0

    for player_name in dataset_player_names:
        best_match, score = process.extractOne(player_name, image_folder_names)

        if score >= MATCH_THRESHOLD:
            print(f"✅ MATCH FOUND (Score: {score}%): Dataset name '{player_name}'  ->  Image folder '{best_match}'")
            
            source_folder_path = os.path.join(IMAGE_DATASET_PATH, best_match)
            source_image_path = find_first_image(source_folder_path)
            
            if source_image_path:
                destination_filename = standardize_name(player_name)
                destination_path = os.path.join(OUTPUT_IMAGE_PATH, destination_filename)
                
                # UPDATED: Instead of copying, resize and save the image
                if resize_and_save_image(source_image_path, destination_path, TARGET_RESOLUTION):
                    print(f"   ➡️  Resized and saved image to '{destination_path}'")
                    success_count += 1
                else:
                    fail_count += 1 # Error is printed inside the function
            else:
                print(f"   ⚠️  WARNING: Matched folder '{best_match}' contains no valid image files.")
                fail_count += 1
        else:
            print(f"❌ NO MATCH: Could not find a suitable match for '{player_name}'. Best attempt was '{best_match}' with score {score}%.")
            fail_count += 1

    # --- 5. Final Report ---
    print("\n--- Process Complete ---")
    print(f"✅ Successfully processed and saved images for {success_count} players.")
    if fail_count > 0:
        print(f"⚠️ Could not find matches or process images for {fail_count} players. Please review the output above.")
    print("------------------------")

if __name__ == "__main__":
    main()