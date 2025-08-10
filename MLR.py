import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

df = pd.read_csv("D:/Batsman_bowler_matchup/data_cleaning/final_dataset1.csv")

df_encoded = pd.get_dummies(df, columns=['batsman', 'bowler'], drop_first=True)

X = df_encoded.drop(columns=['total_runs', 'dismissals', 'strike_rate', 'dismissal_rate'])

target_columns = ['total_runs', 'dismissals', 'strike_rate', 'dismissal_rate']

results = {}

print("Training separate models...\n")

for target in target_columns:
    y = df_encoded[target]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    # Predictions
    y_pred = model.predict(X_test)

    # Evaluation
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    accuracy = model.score(X_test, y_test)
    results[target] = {
        'MSE': mse,
        'MAE': mae,
        'R²': r2,
        'Accuracy': accuracy
    }
    print(f"Model for {target} trained.")
    print(f" MSE: {mse:.2f}"
          f"\n MAE: {mae:.2f}"
          f"\n R² : {r2:.2f}"
          f"\n Accuracy: {accuracy:.2f}\n")

print("Evaluation Results:")
for target, metrics in results.items():
    print(f"--- {target} ---")
    for metric, value in metrics.items():
        print(f" {metric}: {value:.2f}"
              f"\n")
        