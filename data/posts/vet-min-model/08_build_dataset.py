'''
The model to predict whether a player will be out of the league the following year.

I will train the model on data of players who signed veteran minimum contract and see which
attributes contribute the most to players flaming out vs betting on themselves and winning.

Then I will test it on testing data and for the formula that works out best, I will try it on
players on the minimum this year to predict whether they will be in or out of the league next year.

'''

import json
import pandas as pd
from pathlib import Path

ENCODING = "utf-8"

HERE = Path(__file__).parent
DATA = HERE / "../../../web/public/data/kuminga-line"

pd.set_option("display.max_columns", None)


#Loads all the signings where they took pay cuts
with open(DATA / "prove_it.json", encoding=ENCODING) as f:
    data = json.load(f)

df = pd.DataFrame(data["signings"])

print(df.head())

#Load all minimum signings
with open(DATA / "all_signings.json", encoding=ENCODING) as f:
    all_data = json.load(f)

all_signings = pd.DataFrame(all_data["signings"])

print(all_signings.columns.tolist())
print(len(all_signings))

#create a helper df to move years of service into df since prove_it.json doesn't have it
#Each combination of brefId, year, and salary gives a unique vet min signing
#So we need all three so we don't delete data or replace existing data with a duplicate of another signing
helper = all_signings[["brefId", "year", "salary", "yearsOfService"]]
helper = helper.rename(columns={"salary" : "vetMinSalary"})

'''
Use the merge function to add the helper columns to df.
Helper columns are added to the right.
Since both dataframes have brefId, year, and vetMinSalary, on = [...] deletes the second one.
Rows match only when all three values are the same.
how="left" keeps every row in df, and if a row has no match, the new column is blank.
'''
df = df.merge(right=helper, on=["brefId", "year", "vetMinSalary"], how="left")


print(len(df))
print(df.head())
print(df["yearsOfService"].isna().sum())

#add the draft picks of players drafted before 1990 and cap the draft picks at 61
#back then there were way more rounds (i.e. Mario Elie drafted 160th)

old_picks = pd.read_csv(HERE / "old_draft_picks.csv")[["brefId", "pick"]]

df = df.merge(right=old_picks, on=["brefId"], how="left")

#combine draftPick and pick to full_pick
df["full_pick"] = df["draftPick"].fillna(df["pick"])

#add a column for undrafted players since some draftpicks are N/A
df["undrafted"] = df["full_pick"].isna().astype(int)

#fill the N/A draft picks with 61 (Shoutout Pat Spencer) and cap out picks higher than 61 at 61.
df["draft_pick"] = df["full_pick"].fillna(61).clip(upper=61)

df["out_next"] = (df["outcome"] == "flamed_out").astype(int)

print(df["out_next"].sum())

#save the final dataset
df = df.rename(columns={"yearsOfService" : "years_service", "year" : "season"})

final = df[["player", "brefId", "age", "years_service", "draft_pick", "undrafted", "season", "out_next"]]

final.to_csv(HERE / 'dataset.csv', index=False)