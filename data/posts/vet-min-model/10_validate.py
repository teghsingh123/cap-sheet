"""
We can compare V1, V2, and V3 on older seasons, so we can see which version is best without looking at the test set.
If we keep changing features until the test data score goes up, it stops being a fair test, due to overfitting.
This file gives us a place to experiment.
"""

import pandas as pd
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

#also trying decision trees
from sklearn.ensemble import RandomForestClassifier

HERE = Path(__file__).parent

pd.set_option("display.max_columns", None)

df = pd.read_csv(HERE / "dataset.csv")

fit = df[df["season"] < 2012]
val = df[(df["season"] >= 2012) & (df["season"] < 2018)]

print(len(fit))
print(len(val))

V1 = ["age", "years_service", "draft_pick", "undrafted", "season"]
V2 = V1 + ["prev_salary_m", "drop_pct"]
V3 = V2 + ["prev_mpg", "prev_games_pct", "prev_bpm", "missed_prev_season"]
V4 = V3 + ["mpg_change", "bpm_change"]

baseline = (val["out_next"] == 0).mean()
print("Baseline:", baseline)


models = [
    ("Logistic", LogisticRegression(max_iter=5000)),
    ("Forest", RandomForestClassifier(n_estimators=500, min_samples_leaf=10, random_state=42)),
]

for model_name, model in models:
    for name, features in [("V1", V1), ("V2", V2), ("V3", V3), ("V4", V4)]:
        X_train = fit[features]
        y_train = fit["out_next"]

        model.fit(X_train, y_train)

        train_predictions = model.predict(X_train)
        print("Train accuracy:", (train_predictions == y_train).mean())

        X_val = val[features]
        y_val = val["out_next"]

        predictions = model.predict(X_val)
        accuracy = (predictions == y_val).mean()

        print(model_name + " " + name + " accuracy:", accuracy)

        chances = model.predict_proba(X_val)[:, 1]
        print(model_name + " " + name + " ranking:", roc_auc_score(y_val, chances))
