"""
Builds three extra JSON exports for the frontend beyond the core vet-min
cliff scatter:

  all_signings.json  -- every vet-min signing from 04 (processed/
                         vetmin_signings.csv), including ones with no
                         prior-season salary to compare (first vet-min ever)
                         or an actual raise. dropPct is null in those cases.

  prove_it.json       -- for each real salary-cliff vet-min signing, what
                         happened to that player's salary the *next* season:
                         did they climb back above the minimum, or stay there?

  young_fa.json       -- new contracts at any salary signed at 21-25 in the
                         last decade of salary data, for the age-vs-contract-
                         value scatter. Taken from 04's processed/
                         new_contracts.csv, so trades, two-ways and rookie
                         deals are left out by the same rules as everywhere
                         else. Not limited to confirmed unrestricted free
                         agency (that isn't in the source data) -- it's "new
                         deal signed by a 21-25 year old", a reasonable proxy.

The shared data and rules come from data/pipeline/common.py.
"""
import csv, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pipeline"))
from common import bio, draft, by_player, min_scale, RATIO_MIN, is_dead_money_echo

OUT = "../../../web/public/data/kuminga-line"

def read(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ---------- all_signings.json ----------
all_signings = []
for row in read("../../processed/vetmin_signings.csv"):
    drop_pct = float(row["drop_pct"]) if row["drop_pct"] else None
    age = float(row["age_at_signing"])
    all_signings.append({
        "player": row["player"],
        "brefId": row["bref_id"],
        "year": int(row["year"]),
        "age": round(age, 2),
        "yearsOfService": int(row["true_yos"]),
        "prevSalary": round(float(row["prev_salary"])) if row["prev_salary"] else None,
        "salary": round(float(row["salary"])),
        "dropPct": drop_pct,
        "ratioOfMin": float(row["ratio"]),
        "team": row["team"],
        "draftPick": draft.get(row["bref_id"]),
        "isKumingaComp": drop_pct is not None and age < 27 and drop_pct > 50,
    })
all_signings.sort(key=lambda r: r["age"])
with open(f"{OUT}/all_signings.json", "w", encoding="utf-8") as f:
    json.dump({"signings": all_signings}, f, indent=2)
print("all_signings:", len(all_signings))

# ---------- prove_it.json ----------
# Three outcomes for the season after a real vet-min cliff:
#   bounced_back -- landed a real contract again (>1.5x a full minimum)
#   stuck        -- signed another genuine, full-rate-ish minimum deal
#   flamed_out   -- no next-season row at all (out of the league), OR a
#                   next-season row so heavily prorated it's not a reliable
#                   read on a real deal (e.g. Danny Green: signed with
#                   Philly for 2023-24, played 2 games, was waived, and the
#                   $202k on record is a fraction of what his contract was
#                   actually worth). Both cases tell the same story -- his
#                   career petered out that year -- so they're grouped
#                   together rather than either being dropped or being
#                   miscounted as "stuck at a normal minimum job."
#
# Signings from the LAST year the salary data covers are excluded entirely --
# there's categorically no "next season" row available for them regardless
# of what actually happened, so defaulting them to "flamed out" would just
# be mistaking the dataset ending for a real outcome.
LAST_YEAR = max(int(r["year"]) for rows in by_player.values() for r in rows)
prove_it = []
for row in read("../../processed/vetmin_signings.csv"):
    if not row["drop_pct"] or float(row["drop_pct"]) <= 0:
        continue  # only real cliffs -- "did they recover from THIS"
    year = int(row["year"])
    if year >= LAST_YEAR:
        continue  # no next-season data can possibly exist -- not a real outcome
    bref_id = row["bref_id"]
    vetmin_salary = float(row["salary"])
    next_year = year + 1
    player_rows = by_player.get(bref_id, [])
    next_rows = [
        r for r in player_rows
        if int(r["year"]) == next_year
        and not is_dead_money_echo(bref_id, player_rows, r["team"], float(r["salary"]), next_year)
    ]
    next_salary = max((float(r["salary"]) for r in next_rows), default=None)

    b = bio.get(bref_id)
    next_yos = max(0, min(next_year - int(b["year_min"]), 10)) if b else None
    next_min = min_scale.get((next_year, next_yos)) if next_yos is not None else None
    next_reliable = next_salary is not None and (
        next_min is None or next_salary / next_min >= RATIO_MIN
    )

    # compare against the FULL-season minimum, not what a prorated
    # mid-season deal actually paid -- otherwise a normal minimum deal the
    # next year looks like a raise (DeAndre Jordan's prorated $592k with
    # Philly in 2022 was showing as a "bounce back" to his $2.9M Denver
    # minimum). And use the higher of this season's minimum and NEXT
    # season's, which is what a minimum deal would actually pay him then:
    # the scale rises every year and he's gained a year of service. Damon
    # Jones went from a prorated $106k in 1999-00 to $710k, which cleared
    # 1.5x that season's minimum but was only 1.42x the next one's --
    # another minimum-level deal, not a bounce-back.
    full_min = max(vetmin_salary, float(row["min_salary"]), next_min or 0)
    if next_salary is not None and next_reliable:
        outcome = "bounced_back" if next_salary > full_min * 1.5 else "stuck"
    else:
        outcome = "flamed_out"

    prove_it.append({
        "player": row["player"],
        "brefId": bref_id,
        "year": year,
        "age": round(float(row["age_at_signing"]), 2),
        "vetMinSalary": round(vetmin_salary),
        "nextYearSalary": round(next_salary) if (next_salary is not None and next_reliable) else None,
        "multiple": round(next_salary / full_min, 2) if (next_salary is not None and next_reliable) else None,
        "outcome": outcome,
        "draftPick": draft.get(bref_id),
    })
prove_it.sort(key=lambda r: (r["multiple"] is None, -(r["multiple"] or 0)))
with open(f"{OUT}/prove_it.json", "w", encoding="utf-8") as f:
    json.dump({"signings": prove_it}, f, indent=2)
counts = {k: sum(1 for r in prove_it if r["outcome"] == k) for k in ("bounced_back", "stuck", "flamed_out")}
print("prove_it:", len(prove_it), counts)

# ---------- young_fa.json ----------
YEARS = range(2015, 2025)  # last decade of available salary data
young_fa = []
for row in read("../../processed/new_contracts.csv"):
    year, age, salary = int(row["year"]), float(row["age_at_signing"]), float(row["salary"])
    if year not in YEARS or not (21 <= age <= 25):
        continue
    if salary < 300_000:
        continue  # cup-of-coffee / emergency call-up, not a real signing
    young_fa.append({
        "player": row["player"],
        "brefId": row["bref_id"],
        "year": year,
        "age": round(age, 2),
        "salary": round(salary),
        "team": row["team"],
        "draftPick": draft.get(row["bref_id"]),
    })
young_fa.sort(key=lambda r: r["age"])
with open(f"{OUT}/young_fa.json", "w", encoding="utf-8") as f:
    json.dump({"signings": young_fa}, f, indent=2)
print("young_fa:", len(young_fa))
