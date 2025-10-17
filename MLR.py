import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Load encoded dataset
file_path = "D:/Batsman_bowler_matchup/data_cleaning/final/final_dataset.csv"
df = pd.read_csv(file_path)
print("Dataset shape:", df.shape)
print("Columns:", df.columns)

# Features (exclude target columns)
X = df.drop(columns=['total_runs', 'dismissals', 'strike_rate', 'dismissal_rate'])

# Targets
targets = ['total_runs', 'dismissals', 'strike_rate', 'dismissal_rate']

results = {}

for target in targets:
    print(f"\n📊 Training model for: {target}")
    y = df[target]

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # Train Linear Regression model
    model = LinearRegression()
    model.fit(X_train, y_train)

    # Predictions
    y_pred = model.predict(X_test)

    # Evaluation metrics
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    results[target] = {"MSE": mse, "MAE": mae, "R²": r2}

    print(f"--- {target} ---")
    print(f" MSE: {mse:.2f}")
    print(f" MAE: {mae:.2f}")
    print(f" R² : {r2:.2f}")

# Final summary
print("\Final Evaluation Results:")
for target, metrics in results.items():
    print(f"\n--- {target} ---")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.2f}")
