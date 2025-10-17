import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import os

# Load dataset
df = pd.read_csv("D:/Batsman_bowler_matchup/data_cleaning/final/final_dataset.csv")
print("Dataset loaded:", df.shape)

# Create models folder if not exists
os.makedirs("models", exist_ok=True)

# Features & targets
X = df.drop(columns=['total_runs', 'dismissals', 'strike_rate', 'dismissal_rate'])
y_targets = {
    'total_runs': df['total_runs'],
    'dismissals': df['dismissals'],
    'strike_rate': df['strike_rate'],
    'dismissal_rate': df['dismissal_rate']
}

# Train & evaluate for each target
results = {}
for target, y in y_targets.items():
    print(f"\nTraining RandomForest for {target} ...")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=200,      # more trees for better performance
        max_depth=None,       # let trees grow fully
        random_state=42,
        n_jobs=-1             # use all CPU cores
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # Save model as joblib
    model_filename = f"D:/Batsman_bowler_matchup/models/rf_model_{target}.joblib"
    joblib.dump(model, model_filename)
    print(f" Model for {target} saved to {model_filename}")

    # Metrics
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    results[target] = {"MSE": mse, "MAE": mae, "R²": r2}

    print(f"--- {target} ---")
    print(f" MSE: {mse:.2f}")
    print(f" MAE: {mae:.2f}")
    print(f" R² : {r2:.2f}")

