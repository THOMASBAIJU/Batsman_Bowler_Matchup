import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuration ---
# The full path to your final dataset file.
DATASET_PATH = r"D:\Batsman_bowler_matchup\data_cleaning\final\final_dataset.csv"

# The directory where the final model will be saved.
MODELS_DIR = "models"

# The final name for your trained model file.
OUTPUT_MODEL_FILE = os.path.join(MODELS_DIR, "xgb_model_dismissals.joblib")


# --- 1. Load and Prepare the Data ---
print("🔹 Loading dataset...")
df = pd.read_csv(DATASET_PATH)

# For classification, the target column 'dismissals' must be integers (0 or 1).
print("🔹 Preparing data for classification...")
if 'dismissals' in df.columns:
    # MODIFIED: Convert the 'dismissals' column to a binary format.
    # Any value greater than 0 becomes 1 (a dismissal occurred).
    # 0 remains 0 (no dismissal).
    df['dismissals'] = (df['dismissals'] > 0).astype(int)
    print("✅ 'dismissals' column converted to binary (0 or 1).")
else:
    print(f"Error: 'dismissals' column not found in the dataset at {DATASET_PATH}")
    exit() # Stop the script if the target column is missing.

# Define the features (inputs) and the single target (output) for the model.
# This list must match the features your Flask app provides for prediction.
feature_columns = ['batsman', 'bowler', 'total_balls', 'batting_hand', 'bowling_style', 'venue']
X = df[feature_columns]
y = df['dismissals'] # The target is only the 'dismissals' column.


# --- 2. Split Data into Training and Testing Sets ---
print("🔹 Splitting data into training and testing sets...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)


# --- 3. Initialize and Train the XGBoost Classifier ---
print("🔹 Initializing and training the XGBClassifier model...")
# These are standard parameters for a binary classification task.
model = XGBClassifier(
    objective='binary:logistic',  # Specifies that this is a yes/no prediction.
    eval_metric='logloss',        # A common performance metric for this type of model.
    n_estimators=200,
    learning_rate=0.1,
    max_depth=5,
    use_label_encoder=False,      # Suppresses a common warning.
    random_state=42
)

# Train the model on your training data.
model.fit(X_train, y_train)
print("✅ Model training complete.")


# --- 4. Save the Trained Model to a .joblib File ---
# First, ensure the 'models' directory exists.
print(f"🔹 Saving the model to the '{MODELS_DIR}' directory...")
os.makedirs(MODELS_DIR, exist_ok=True)

# Save the trained model object to the specified file.
joblib.dump(model, OUTPUT_MODEL_FILE)
print(f"✅ Model successfully saved to: {OUTPUT_MODEL_FILE}")


# --- 5. Evaluate Model Performance ---
print("\n🔹 Evaluating model performance on the unseen test set...")
preds = model.predict(X_test)
accuracy = accuracy_score(y_test, preds)

print(f"📊 Model Accuracy on Test Data: {accuracy:.2f}")
print("\nClassification Report:")
print(classification_report(y_test, preds))

# --- NEW: Generate and display the confusion matrix heatmap ---
print("\n🔹 Generating Confusion Matrix Heatmap...")
cm = confusion_matrix(y_test, preds)

# Create a heatmap figure
plt.figure(figsize=(8, 6))
sns.heatmap(cm, 
            annot=True,      # Show the numbers in each cell
            fmt='d',         # Format the numbers as integers
            cmap='Blues',    # Color scheme
            xticklabels=['Not Out (0)', 'Out (1)'], 
            yticklabels=['Not Out (0)', 'Out (1)'])
plt.ylabel('Actual Label')
plt.xlabel('Predicted Label')
plt.title('Confusion Matrix for Dismissals')

# Display the plot in a new window
plt.show()
print("✅ Heatmap window displayed.")

