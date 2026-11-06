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

#small only has pay cuts, big also has the extra signings
fit_small = df[(df["season"] < 2012) & (df["pay_cut"] == 1)]
fit_big = df[df["season"] < 2012]

#validation stays pay cuts only since that's the question we're answering
val = df[(df["season"] >= 2012) & (df["season"] < 2018) & (df["pay_cut"] == 1)]

print(len(fit_small))
print(len(fit_big))
print(len(val))

V1 = ["age", "years_service", "draft_pick", "undrafted", "season"]
V2 = V1 + ["prev_salary_m", "drop_pct"]
V3 = V2 + ["prev_mpg", "prev_games_pct", "prev_bpm", "missed_prev_season"]
V4 = V3 + ["mpg_change", "bpm_change"]
V5 = V3 + ["pay_cut", "no_prev_salary"]

baseline = (val["out_next"] == 0).mean()
print("Baseline:", baseline)


models = [
    ("Logistic", LogisticRegression(max_iter=5000)),
    ("Forest", RandomForestClassifier(n_estimators=500, min_samples_leaf=10, random_state=42)),
]

#the two setups we're comparing
#each one picks its own training data and features
runs = [
    ("Small V3", fit_small, V3),
    ("Big V5", fit_big, V5),
]

for name, fit, features in runs:
    X_train = fit[features]
    y_train = fit["out_next"]

    #create a new forest each run so the two don't share anything
    model = RandomForestClassifier(n_estimators=500, min_samples_leaf=10, random_state=42)
    model.fit(X_train, y_train)

    #check how it does on the data it learned from
    train_predictions = model.predict(X_train)
    print(name + " train accuracy:", (train_predictions == y_train).mean())

    #val is pay cuts only for both runs so the scores can be compared
    X_val = val[features]
    y_val = val["out_next"]

    #accuracy uses the yes/no predictions
    predictions = model.predict(X_val)
    print(name + " accuracy:", (predictions == y_val).mean())

    #ranking uses each player's chance of being out, not the yes/no
    chances = model.predict_proba(X_val)[:, 1]
    print(name + " ranking:", roc_auc_score(y_val, chances))