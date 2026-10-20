"""
Builds three extra JSON exports for the frontend beyond the core vet-min
cliff scatter:

  all_signings.json  -- every flagged vet-min signing (yos>=1, new stint),
                         including ones with no prior-season salary to compare
                         (first vet-min ever) or an actual raise (e.g. coming
                         off a two-way year). dropPct is null in those cases.

  prove_it.json       -- for each real salary-cliff vet-min signing, what
                         happened to that player's salary the *next* season:
                         did they climb back above the minimum, or stay there?

  young_fa.json       -- age 21-25 "new contract" signings (new team or a
                         real gap year -- same definition used elsewhere in
                         this pipeline) from the last decade of salary data,
                         at any salary level, for the age-vs-contract-value
                         scatter. This is NOT filtered to confirmed
                         unrestricted free agency (that designation isn't in
                         the source data) -- it's "new deal signed by a
                         21-25 year old", which is a reasonable proxy.
"""
import csv, datetime, json

bio = {}
with open("../../processed/player_bios.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        bio[row["bref_id"]] = row

min_scale = {}
with open("../../processed/salary_min_scale.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        start, _ = row["season"].split("-")
        end_year = int(start) + 1
        min_scale[(end_year, int(row["years_of_service"]))] = int(row["min_salary"])

RATIO_MIN = 0.22  # same "not a real signing" floor used in 04_build_vetmin_signings.py

# a (team, salary) pair that closely matches one from an EARLIER season for
# the same player is almost certainly stretched dead money still being paid
# out (e.g. a player traded into a "salary dump" and immediately stretched --
# DeAndre Jordan's ~$7.9M Detroit cap hit in 2022 shows up again, barely
# changed, in 2023 even though he was never on Detroit's roster that year),
# not a fresh salary actually earned that season. Only counts if that
# earlier season also shows the player with ANOTHER team at the same time --
# the actual signature of a trade-then-cut churn year, as opposed to a
# normal player just staying on one team for a few seasons on a flat-ish
# salary (which would otherwise false-positive constantly) -- AND the
# candidate salary itself is clearly above a normal minimum-level deal.
# Without that second guard, a player re-signing consecutive real vet-min
# deals with the SAME team (whose value legitimately rises ~5-10%/year on
# the minimum scale) gets misflagged whenever an UNRELATED dead-money row
# from a totally different team also happens to exist that season -- that's
# exactly what happened to Jordan's real 2023->2024 Denver re-signing before
# this guard was added.
def looks_like_min_level(bref_id, year, salary):
    b = bio.get(bref_id)
    if not b:
        return False
    yos = max(0, min(year - int(b["year_min"]), 10))
    min_sal = min_scale.get((year, yos))
    return min_sal is not None and salary / min_sal <= 1.15

def is_dead_money_echo(bref_id, player_rows, team, salary, before_year, tol=0.15):
    if looks_like_min_level(bref_id, before_year, salary):
        return False
    for r in player_rows:
        ry = int(r["year"])
        if ry < before_year and r["team"] == team:
            rs = float(r["salary"])
            if rs > 0 and abs(salary - rs) / rs < tol:
                other_teams = {rr["team"] for rr in player_rows if int(rr["year"]) == ry} - {team}
                if other_teams:
                    return True
    return False

draft = {}
with open("../../processed/draft_picks.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        draft[row["bref_id"]] = int(row["pick"])

by_player = {}
with open("../../source/salary_history.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        by_player.setdefault(row["bref_id"], []).append(row)
for rows in by_player.values():
    rows.sort(key=lambda r: int(r["year"]))

def age_at(bref_id, year):
    b = bio.get(bref_id)
    if not b:
        return None
    birth = datetime.date.fromisoformat(b["birth_date"])
    season_start = datetime.date(year - 1, 10, 1)
    return round((season_start - birth).days / 365.25, 2)

# ---------- all_signings.json ----------
all_signings = []
with open("../../processed/vetmin_signings.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
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
with open("../../../web/public/data/kuminga-line/all_signings.json", "w", encoding="utf-8") as f:
    json.dump({"signings": all_signings}, f, indent=2)
print("all_signings:", len(all_signings))

# ---------- prove_it.json ----------
# Three outcomes for the season after a real vet-min cliff:
#   bounced_back -- landed a real contract again (>1.5x the vet-min rate)
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
with open("../../processed/vetmin_signings.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
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
with open("../../../web/public/data/kuminga-line/prove_it.json", "w", encoding="utf-8") as f:
    json.dump({"signings": prove_it}, f, indent=2)
counts = {k: sum(1 for r in prove_it if r["outcome"] == k) for k in ("bounced_back", "stuck", "flamed_out")}
print("prove_it:", len(prove_it), counts)

# ---------- young_fa.json ----------
YEARS = range(2015, 2025)  # last decade of available salary data
young_fa = []
for bref_id, rows in by_player.items():
    b = bio.get(bref_id)
    if not b:
        continue
    teams_by_year = {}
    for row in rows:
        teams_by_year.setdefault(int(row["year"]), set()).add(row["team"])
    for row in rows:
        year = int(row["year"])
        if year not in YEARS:
            continue
        age = age_at(bref_id, year)
        if age is None or not (21 <= age <= 25):
            continue
        prev_teams = teams_by_year.get(year - 1)
        is_new_stint = prev_teams is None or row["team"] not in prev_teams
        if not is_new_stint:
            continue
        salary = float(row["salary"])
        if salary < 300_000:
            continue  # cup-of-coffee / emergency call-up, not a real signing
        young_fa.append({
            "player": row["player"],
            "brefId": bref_id,
            "year": year,
            "age": age,
            "salary": round(salary),
            "team": row["team"],
            "draftPick": draft.get(bref_id),
        })
young_fa.sort(key=lambda r: r["age"])
with open("../../../web/public/data/kuminga-line/young_fa.json", "w", encoding="utf-8") as f:
    json.dump({"signings": young_fa}, f, indent=2)
print("young_fa:", len(young_fa))
