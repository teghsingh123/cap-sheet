import csv, datetime

# --- load bio: true debut year + birthdate ---
bio = {}
with open("../processed/player_bios.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        bio[row["bref_id"]] = row

# --- load min salary scale ---
min_scale = {}
with open("../processed/salary_min_scale.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        start, _ = row["season"].split("-")
        end_year = int(start) + 1
        min_scale[(end_year, int(row["years_of_service"]))] = int(row["min_salary"])

# --- load all salary rows, grouped by player, so we can tell a *new* contract
#     stint (team changed, or a gap year) from just another season of an
#     existing multi-year deal riding the minimum scale up ---
by_player = {}
with open("../source/salary_history.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        by_player.setdefault(row["bref_id"], []).append(row)

for bref_id, rows in by_player.items():
    rows.sort(key=lambda r: int(r["year"]))

# a (team, salary) pair that closely matches one from an EARLIER season for
# the same player is almost certainly stretched dead money still being paid
# out, not a fresh salary for that team -- see the note below where this is
# used. Only counts if that earlier season also shows the player with
# ANOTHER team at the same time -- the actual signature of a trade-then-cut
# churn year, as opposed to a normal player just staying on one team for a
# few seasons on a flat-ish salary (which would otherwise false-positive
# constantly, since real contracts don't escalate much year to year either)
# -- AND the candidate salary itself is clearly above a normal minimum-level
# deal, since a legitimate back-to-back veteran-minimum re-signing with the
# same team (which rises ~5-10%/year on the scale) would otherwise get
# misflagged whenever an unrelated dead-money row from a different team
# happens to also exist that season.
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

# Minimum salary is a legal floor for a *full* season. A player signed
# mid-season (waiver pickup, post-buyout, 10-day-turned-rest-of-season) gets
# that same minimum rate but prorated for games remaining, so their total pay
# can land well below the full-season number while still being a genuine
# vet-min signing. So instead of a tight symmetric band around the full-season
# number, allow anything from a small floor (filters out things like single
# emergency call-ups) up to just above the full number.
RATIO_MAX = 1.03
RATIO_MIN = 0.22  # ~1/4 season minimum; below this it's an emergency/cup-of-coffee deal, not a real signing
flagged = []
skipped_no_bio = 0
skipped_same_stint = 0
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
            continue  # skip rookie-min (yos 0) and glitches (yos<0)
        yos_capped = min(yos, 10)
        key = (year, yos_capped)
        if key not in min_scale:
            continue
        min_sal = min_scale[key]
        salary = float(row["salary"])
        if min_sal == 0:
            continue
        ratio = salary / min_sal
        if ratio > RATIO_MAX or ratio < RATIO_MIN:
            continue

        prev_teams = teams_by_year.get(year - 1)
        is_new_stint = prev_teams is None or row["team"] not in prev_teams
        if not is_new_stint:
            skipped_same_stint += 1
            continue  # just another year of an existing contract, not a new min signing

        birth = datetime.date.fromisoformat(b["birth_date"])
        season_start = datetime.date(year - 1, 10, 1)
        age = (season_start - birth).days / 365.25

        # "salary cliff": what did they earn last season, before this min deal?
        # Exclude rows that are "dead money echoes" -- a near-identical
        # (team, salary) pair already appeared in an EARLIER season for this
        # player. That's the signature of a stretched waiver: e.g. DeAndre
        # Jordan was traded to Detroit in 2022 and immediately stretched, so
        # his ~$7.9M Detroit cap hit shows up again in 2023 even though he
        # was never actually on Detroit's roster that year and received no
        # new money -- it's the same old obligation still being paid out.
        # Using that as "what he earned last year" wildly overstates the
        # real cliff (or understates it, on the other side of the ledger).
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
            "team": row["team"], "birth_date": b["birth_date"], "age_at_signing": round(age, 2),
            "prev_salary": prev_salary, "drop_pct": drop_pct,
        })

flagged.sort(key=lambda r: r["age_at_signing"])
with open("../processed/vetmin_signings.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "player", "bref_id", "year", "true_yos", "salary", "min_salary",
        "team", "birth_date", "age_at_signing", "prev_salary", "drop_pct", "ratio",
    ])
    w.writeheader()
    w.writerows(flagged)

print("salary rows skipped (no bio match):", skipped_no_bio)
print("skipped (same stint, not a new signing):", skipped_same_stint)
print("flagged vet-min rows (yos>=1, new stint):", len(flagged))
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
