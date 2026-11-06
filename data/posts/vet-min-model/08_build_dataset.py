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
PROCESSED = HERE / "../../processed/vet-min-model"
DATA = HERE / "../../../web/public/data/kuminga-line"

pd.set_option("display.max_columns", None)


#Loads all the signings where they took pay cuts
with open(DATA / "prove_it.json", encoding=ENCODING) as f:
    data = json.load(f)

df = pd.DataFrame(data["signings"])

print(df.head())

#Since we added non paycut vet mins for training, add pay_cut as a feature
df["pay_cut"] = 1
extra = pd.read_csv(PROCESSED / "extra_signings.csv")
extra["pay_cut"] = 0
df = pd.concat([df, extra], ignore_index=True)

#Load all minimum signings
with open(DATA / "all_signings.json", encoding=ENCODING) as f:
    all_data = json.load(f)

all_signings = pd.DataFrame(all_data["signings"])

print(all_signings.columns.tolist())
print(len(all_signings))

#create a helper df to move years of service into df since prove_it.json doesn't have it
#Each combination of brefId, year, and salary gives a unique vet min signing
#So we need all three so we don't delete data or replace existing data with a duplicate of another signing
helper = all_signings[["brefId", "year", "salary", "yearsOfService", "prevSalary", "dropPct"]]
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

old_picks = pd.read_csv(PROCESSED / "old_draft_picks.csv")[["brefId", "pick"]]

df = df.merge(right=old_picks, on=["brefId"], how="left")

#combine draftPick and pick to full_pick
df["full_pick"] = df["draftPick"].fillna(df["pick"])

#add a column for undrafted players since some draftpicks are N/A
df["undrafted"] = df["full_pick"].isna().astype(int)

#fill the N/A draft picks with 61 (Shoutout Pat Spencer) and cap out picks higher than 61 at 61.
df["draft_pick"] = df["full_pick"].fillna(61).clip(upper=61)

df["out_next"] = (df["outcome"] == "flamed_out").astype(int)

print(df["out_next"].sum())

df["no_prev_salary"] = df["prevSalary"].isna().astype(int)

#previous salary in millions
df["prev_salary_m"] = df["prevSalary"] / 1000000
df["prev_salary_m"] = df["prev_salary_m"].fillna(0)

df["prev_season"] = df["year"] - 1

stats = pd.read_csv(PROCESSED / "season_stats.csv")
df = df.merge(right=stats, on=["brefId", "prev_season"], how="left")
print(len(df))

df["missed_prev_season"] = df["prev_mpg"].isna().astype(int)

#replace missing values with defaults
df["prev_mpg"] = df["prev_mpg"].fillna(0)
df["prev_bpm"] = df["prev_bpm"].fillna(-2)
df["prev_games_pct"] = df["prev_games_pct"].fillna(0)

#using data from 2 years prior for further experimenting with the model

df["prev2_season"] = df["year"] - 2

stats2 = stats.rename(columns={"prev_season" : "prev2_season", "prev_mpg": "prev2_mpg", "prev_bpm" : "prev2_bpm"})
stats2 = stats2.drop(columns=["prev_games_pct"])

df = df.merge(right=stats2, on=["brefId", "prev2_season"],how="left")
print(len(df))

df["mpg_change"] = df["prev_mpg"] - df["prev2_mpg"]
df["bpm_change"] = df["prev_bpm"] - df["prev2_bpm"]

df["mpg_change"] = df["mpg_change"].fillna(0)
df["bpm_change"] = df["bpm_change"].fillna(0)

dates = pd.read_csv(PROCESSED / "signing_dates.csv")
df = df.merge(right=dates,on=["brefId", "year", "vetMinSalary"],how="left")
print(len(df))

df["signing_date"] = pd.to_datetime(df["signing_date"])

july1 = pd.to_datetime((df["year"] - 1).astype(str) + ("-07-01"))
df["days_after_july1"] = (df["signing_date"] - july1).dt.days

df["days_after_july1"] = df["days_after_july1"].fillna(-1)

#real stats of the players before signing
box = pd.read_csv(PROCESSED / "box_stats.csv")
df = df.merge(right=box,on=["brefId", "prev_season"],how="left")
print(len(df))

#counting stats are 0 for a missed season, the rest get a typical fringe player's value
df = df.fillna({
    "prev_ppg": 0, "prev_rpg": 0, "prev_apg": 0, "prev_spg": 0, "prev_bpg": 0, "prev_tov": 0,
    "prev_start_pct": 0, "prev_vorp": 0, "prev_ts": 0.5, "prev_3pa_rate": 0.2, "prev_usg": 18,
    "prev_ws48": 0.05, "prev_obpm": -1.5, "prev_dbpm": -0.5,
})


#save the final dataset
df = df.rename(columns={"yearsOfService" : "years_service", "year" : "season", "dropPct" : "drop_pct"})

df["drop_pct"] = df["drop_pct"].fillna(0).clip(lower=0)

final = df[["player", "brefId", "age", "years_service", "draft_pick", "undrafted", "season", "out_next", "prev_salary_m", "drop_pct", "prev_season", "missed_prev_season", "prev_mpg", "prev_games_pct", "prev_bpm", "mpg_change", "bpm_change", "pay_cut", "no_prev_salary", "days_after_july1", "prev_ppg", "prev_rpg", "prev_apg", "prev_spg", "prev_bpg", "prev_tov", "prev_start_pct",
       "prev_ts", "prev_3pa_rate", "prev_usg", "prev_ws48", "prev_obpm", "prev_dbpm", "prev_vorp"]]

final.to_csv(PROCESSED / "dataset.csv", index=False)