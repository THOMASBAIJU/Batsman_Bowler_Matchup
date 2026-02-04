import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
# Updated metrics import to include all requested evaluations
from sklearn.metrics import (
    accuracy_score, roc_auc_score, confusion_matrix,
    classification_report, precision_score, recall_score, f1_score,
    roc_curve  # <-- Added roc_curve import
)
import joblib
import os
# Imports for visualization
import seaborn as sns
import matplotlib.pyplot as plt

# --- Configuration ---
DATASET_PATH = "final_dataset.csv"
MODELS_DIR = "../models"
MODEL_FILENAME = os.path.join(MODELS_DIR, "rf_model_dismissals.joblib")

def train_bowler_model_rf():
    """
    Trains a Random Forest model to predict the probability of a dismissal.
    This model is the responsibility of the Bowler Prediction Team.
    """
    print(" BOWLING TEAM (Random Forest) SCRIPT ".center(60, "="))
    
    # --- 1. Load Data ---
    print(f"🔹 Loading dataset from '{DATASET_PATH}'...")
    os.makedirs(MODELS_DIR, exist_ok=True)
    try:
        df = pd.read_csv(DATASET_PATH)
    except FileNotFoundError:
        print(f"❌ ERROR: Dataset not found. Please ensure '{DATASET_PATH}' is correct relative to your script location.")
        return

    # --- 2. Define Features and Target ---
    feature_columns = ['batsman', 'bowler', 'batting_hand', 'bowling_style', 'venue']
    target_column = 'is_dismissed'

    df[target_column] = (df['dismissals'] > 0).astype(int)
    
    X = df[feature_columns]
    y = df[target_column]
    print("✅ Features and target defined for predicting dismissals.")

    # --- 3. Split Data ---
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    print("🔹 Data split into training (80%) and testing (20%) sets.")

    # --- 4. Train Random Forest Classifier Model ---
    print(f"☑️  Training RandomForestClassifier for '{target_column}'...")
    model = RandomForestClassifier(random_state=42, n_estimators=150, n_jobs=-1)
    model.fit(X_train, y_train)

    # --- 5. Evaluate Model ---
    preds = model.predict(X_test)
    pred_proba = model.predict_proba(X_test)[:, 1]

    # --- Detailed Metrics ---
    print("\n" + " MODEL EVALUATION ".center(50, "-"))
    
    # Calculate metrics
    acc = accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, pred_proba)
    # Note: These metrics are for the positive class (1 = 'Dismissed') by default
    precision = precision_score(y_test, preds)
    recall = recall_score(y_test, preds)
    f1 = f1_score(y_test, preds)
    
    # Print simple metrics
    print(f"  🔹 Accuracy:    {acc:.4f}")
    print(f"  🔹 AUC Score:   {auc:.4f}")
    print(f"  🔹 Precision:   {precision:.4f} (For 'Dismissed')")
    print(f"  🔹 Recall:      {recall:.4f} (For 'Dismissed')")
    print(f"  🔹 F1 Score:    {f1:.4f} (For 'Dismissed')")

    # Classification Report
    print("\n" + " Classification Report ".center(50, "-"))
    report = classification_report(y_test, preds, target_names=['Not Dismissed (0)', 'Dismissed (1)'])
    print(report)

    # Confusion Matrix Heatmap
    print("\n" + " Confusion Matrix ".center(50, "-"))
    cm = confusion_matrix(y_test, preds)
    
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Not Dismissed (0)', 'Dismissed (1)'], 
                yticklabels=['Not Dismissed (0)', 'Dismissed (1)'])
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.title('Confusion Matrix for Dismissal Prediction')
    plt.show() # This will display the plot in a new window
    
    print("Confusion Matrix plot displayed.")
    print("-" * 50)

    # --- START: Added code for ROC Curve ---
    print("\n" + " ROC Curve ".center(50, "-"))
    
    # Calculate FPR (False Positive Rate) and TPR (True Positive Rate)
    fpr, tpr, thresholds = roc_curve(y_test, pred_proba)

    # Plot the ROC curve
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='blue', label=f'ROC Curve (AUC = {auc:.4f})')
    plt.plot([0, 1], [0, 1], color='red', linestyle='--', label='Random Guess (AUC = 0.5)')
    
    # Customize the plot
    plt.xlabel('False Positive Rate (FPR)')
    plt.ylabel('True Positive Rate (TPR)')
    plt.title('Receiver Operating Characteristic (ROC) Curve')
    plt.legend(loc="lower right")
    plt.grid(True)
    plt.show() # This will display the plot in a new window
    
    print("ROC Curve plot displayed.")
    print("-" * 50)
    # --- END: Added code for ROC Curve ---


    # --- 6. Save Model ---
    joblib.dump(model, MODEL_FILENAME)
    print(f"\n✅ Model saved successfully to '{MODEL_FILENAME}'")
    print("=" * 60)

if __name__ == '__main__':
    train_bowler_model_rf()