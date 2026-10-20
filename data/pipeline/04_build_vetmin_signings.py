import csv
from common import (bio, by_player, min_scale, RATIO_MIN, RATIO_MAX, new_contract_team,
                    age_at_signing, signing_date, is_dead_money_echo)

# Two outputs:
#   processed/new_contracts.csv  -- every new contract (any salary) signed by a
#                                   player with at least a year of service.
#                                   Per-post scripts read it instead of
#                                   re-deciding what a new contract is.
#   processed/vetmin_signings.csv -- the subset at minimum level: the
#                                   veteran-minimum signings.
new_contracts = []
flagged = []
skipped_no_bio = 0
skipped = {"same_stint": 0, "carried": 0, "two_way": 0}
credited_to_signing_team = 0
for bref_id, rows in by_player.items():
    b = bio.get(bref_id)
    if not b:
        skipped_no_bio += len(rows)
        continue
    debut_year = int(b["year_min"])
    # teams played for, per year (a player can have >1 row in a year if traded)
    teams_by_year = {}
    for row in rows:
        teams_by_year.setdefault(int(row["year"]), set()).add(row["team"])

    for row in rows:
        year = int(row["year"])
        yos = year - debut_year
        if yos < 1:
            continue  # rookie deals (yos 0) and glitches (yos < 0) aren't new contracts here

        # is it a new contract, and which team signed it? (rules in common.py)
        team, why_not = new_contract_team(bref_id, year, row["team"], teams_by_year)
        if team is None:
            assert why_not is not None  # always set when team is None
            skipped[why_not] += 1
            continue
        credited_to_signing_team += team != row["team"]
        salary = float(row["salary"])
        age = age_at_signing(bref_id, year, team)
        new_contracts.append({
            "player": row["player"], "bref_id": bref_id, "year": year, "true_yos": yos,
            "team": team, "salary": salary, "age_at_signing": round(age, 2),
        })

        # veteran minimum: at minimum level for his years of service
        yos_capped = min(yos, 10)
        min_sal = min_scale.get((year, yos_capped))
        if not min_sal:
            continue
        ratio = salary / min_sal
        if ratio > RATIO_MAX or ratio < RATIO_MIN:
            continue

        # "salary cliff": what did he earn last season, before this min deal?
        # Leave out dead-money echoes (see is_dead_money_echo): using a
        # stretched old obligation as "what he earned last year" wildly
        # overstates the real cliff.
        prev_rows = [
            r for r in rows
            if int(r["year"]) == year - 1
            and not is_dead_money_echo(bref_id, rows, r["team"], float(r["salary"]), year - 1)
        ]
        prev_salary = max((float(r["salary"]) for r in prev_rows), default=None)
        drop_pct = None
        if prev_salary and prev_salary > 0:
            drop_pct = round((prev_salary - salary) / prev_salary * 100, 1)

        flagged.append({
            "player": row["player"], "bref_id": bref_id, "year": year,
            "true_yos": yos, "salary": salary, "min_salary": min_sal, "ratio": round(ratio, 3),
            "team": team, "birth_date": b["birth_date"], "age_at_signing": round(age, 2),
            "prev_salary": prev_salary, "drop_pct": drop_pct,
        })

# A pay cut only counts once: the first time a player falls to the minimum.
# If he was already on a minimum deal -- earlier the same season (DeAndre
# Jordan: Lakers in September 2021, then Philadelphia in March 2022) or the
# season before (Anthony Bennett: Toronto 2015-16, then Brooklyn 2016-17) --
# a later minimum signing still counts as a signing, but has no drop. Measured
# the usual way, its "drop" comes from buyout or stretched money (Bennett's
# $3.65M Minnesota buyout) or from a salary he'd already lost, and the same
# fall would show up on the charts twice.
by_season = {}
for r in flagged:
    by_season.setdefault((r["bref_id"], r["year"]), []).append(r)
skipped_repeat_drop = 0
for (bref_id, year), rs in by_season.items():
    # same season: order by signing date; the first deal keeps its drop. A
    # signing with no date in the log goes last, bigger share of the minimum first
    rs.sort(key=lambda r: (signing_date(bref_id, year, r["team"]) or "9999", -r["ratio"]))
    already_min = (bref_id, year - 1) in by_season
    for i, r in enumerate(rs):
        if (i > 0 or already_min) and r["drop_pct"] is not None:
            r["drop_pct"] = None
            skipped_repeat_drop += 1

with open("../processed/new_contracts.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["player", "bref_id", "year", "true_yos", "team", "salary", "age_at_signing"])
    w.writeheader()
    w.writerows(sorted(new_contracts, key=lambda r: (r["year"], r["player"])))

flagged.sort(key=lambda r: r["age_at_signing"])
with open("../processed/vetmin_signings.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "player", "bref_id", "year", "true_yos", "salary", "min_salary",
        "team", "birth_date", "age_at_signing", "prev_salary", "drop_pct", "ratio",
    ])
    w.writeheader()
    w.writerows(flagged)

print("salary rows skipped (no bio match):", skipped_no_bio)
print("skipped (same team, same deal):", skipped["same_stint"])
print("skipped (arrived by trade/claim/expansion, not signed):", skipped["carried"])
print("skipped (two-way contract):", skipped["two_way"])
print("credited to the team that signed him (salary data had the trade partner):", credited_to_signing_team)
print("new contracts (any salary):", len(new_contracts))
print("drop cleared (already on a minimum deal):", skipped_repeat_drop)
print("flagged vet-min rows:", len(flagged))
print()
print("Youngest 20 vet-min signings:")
for r in flagged[:20]:
    print(f"{r['age_at_signing']:.2f}  {r['player']:25s} {r['year']}  YOS={r['true_yos']:2d}  ${r['salary']:,.0f}  {r['team']}")

print()
print("Biggest 'salary cliff' vet-min signings (had real money the year before):")
cliffs = [r for r in flagged if r["drop_pct"] is not None]
cliffs.sort(key=lambda r: -r["drop_pct"])
for r in cliffs[:20]:
    print(f"{r['drop_pct']:5.1f}% drop  {r['player']:22s} {r['year']}  ${r['prev_salary']:,.0f} -> ${r['salary']:,.0f}  age {r['age_at_signing']:.1f}  {r['team']}")

print()
print("'Kuminga comps': age < 27 AND prior-season drop > 50%, youngest first")
comps = [r for r in flagged if r["drop_pct"] is not None and r["drop_pct"] > 50 and r["age_at_signing"] < 27]
comps.sort(key=lambda r: r["age_at_signing"])
for r in comps:
    print(f"{r['age_at_signing']:5.2f}  {r['player']:22s} {r['year']}  ${r['prev_salary']:,.0f} -> ${r['salary']:,.0f}  ({r['drop_pct']:.1f}% drop)  {r['team']}")

with open("../processed/kuminga_comps.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "player", "bref_id", "year", "true_yos", "salary", "min_salary",
        "team", "birth_date", "age_at_signing", "prev_salary", "drop_pct", "ratio",
    ])
    w.writeheader()
    w.writerows(comps)
