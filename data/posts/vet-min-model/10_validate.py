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
PROCESSED = HERE / "../../processed/vet-min-model"

pd.set_option("display.max_columns", None)

df = pd.read_csv(PROCESSED / "dataset.csv")

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
V6 = V3 + ["days_after_july1"]

BOX = ["prev_ppg", "prev_rpg", "prev_apg", "prev_spg", "prev_bpg", "prev_tov", "prev_start_pct",
       "prev_ts", "prev_3pa_rate", "prev_usg", "prev_ws48", "prev_obpm", "prev_dbpm", "prev_vorp"]
V7 = V6 + BOX


pay_cuts = df[df["pay_cut"] == 1]

for cutoff in [2006, 2009, 2012, 2015]:

    fit = pay_cuts[pay_cuts["season"] < cutoff]
    val = pay_cuts[(pay_cuts["season"] >= cutoff) & (pay_cuts["season"] < cutoff + 3)]

    
    baseline = (val["out_next"] == 0).mean()
    print(cutoff, len(fit), len(val), "Baseline:", baseline)

    for name, features in (("V6", V6), ("V7", V7)):

        accuracies = []
        rankings = []

        X_train = fit[features]
        y_train = fit["out_next"]

        #val is pay cuts only for both runs so the scores can be compared
        X_val = val[features]
        y_val = val["out_next"]

        #average over 5 seeds so one lucky forest can't decide the result
        for seed in range(1,6):

            model = RandomForestClassifier(n_estimators=500, min_samples_leaf=10, random_state=seed)
            model.fit(X_train, y_train)

            #accuracy uses the yes/no predictions
            predictions = model.predict(X_val)
            accuracies.append((predictions == y_val).mean())

            #ranking uses each player's chance of being out, not the yes/no
            chances = model.predict_proba(X_val)[:, 1]
            rankings.append(roc_auc_score(y_val, chances))

        #see which columns the last forest leaned on most
        if name == "V7":
            importance = pd.Series(model.feature_importances_, index=features)
            print(importance.sort_values(ascending=False).head(8).round(3))


        print(name, "average accuracy:", sum(accuracies) / len(accuracies))
        print(name, "average ranking:", sum(rankings) / len(rankings))