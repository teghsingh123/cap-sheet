"""
Now that we have our finalized dataset, we will train the model on it.
"""

import pandas as pd
from pathlib import Path

from sklearn.linear_model import LogisticRegression

HERE = Path(__file__).parent

pd.set_option("display.max_columns", None)

#set the df as the csv created at the end of 08
df = pd.read_csv(HERE / "dataset.csv")

print(len(df))
print(df.head())

#split the data into training and testing data

train = df[df["season"] < 2018]
test = df[df["season"] >= 2018]

print(len(train))
print(len(test))

FEATURES = ["age", "years_service", "draft_pick", "undrafted", "season"]

baseline = (test["out_next"] == 0).mean()

X_train = train[FEATURES]
y_train = train["out_next"]

model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

X_test = test[FEATURES]
y_test = test["out_next"]

predictions = model.predict(X_test)
accuracy = (predictions == y_test).mean()

print("Baseline: " + str(baseline))
print("Accuracy: " + str(accuracy))

print(predictions.sum())
for name, weight in zip(FEATURES, model.coef_[0]):
    print(name + ": ", round(float(weight), 3))