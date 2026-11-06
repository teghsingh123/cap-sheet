"""
Labels the minimum signings that aren't pay cuts, so the model can train on them.

prove_it.json only covers pay cuts. This applies the same "out next season" rule
to every other signing in vetmin_signings.csv and writes extra_signings.csv, with
the same columns 08_build_dataset.py reads from prove_it.json.

The rule below is copied from ../kuminga-line/05_build_extra_charts.py, so before
writing anything this checks that it gives the same answer on every signing in
prove_it.json. If the two ever drift apart, the script stops.

Only for training. Validation and test stay pay cuts only.
"""
import csv, json, sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "../../pipeline"))
from common import bio, draft, by_player, min_scale, RATIO_MIN, is_dead_money_echo

SIGNINGS = HERE / "../../processed/vetmin_signings.csv"
PROVE_IT = HERE / "../../../web/public/data/kuminga-line/prove_it.json"
OUT = HERE / "extra_signings.csv"

LAST_YEAR = max(int(r["year"]) for rows in by_player.values() for r in rows)


def outcome(row):
    bref_id, year = row["bref_id"], int(row["year"])
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

    full_min = max(float(row["salary"]), float(row["min_salary"]), next_min or 0)
    if next_salary is not None and next_reliable:
        return "bounced_back" if next_salary > full_min * 1.5 else "stuck"
    return "flamed_out"


with open(SIGNINGS, encoding="utf-8") as f:
    signings = [r for r in csv.DictReader(f) if int(r["year"]) < LAST_YEAR]

prove_it = json.loads(PROVE_IT.read_text(encoding="utf-8"))["signings"]
known = {(s["brefId"], s["year"], s["vetMinSalary"]): s["outcome"] for s in prove_it}

extras, checked = [], 0
for row in signings:
    key = (row["bref_id"], int(row["year"]), round(float(row["salary"])))
    result = outcome(row)
    if key in known:
        if result != known[key]:
            sys.exit(f"Rule doesn't match prove_it.json for {key}: {result} vs {known[key]}")
        checked += 1
    else:
        extras.append({
            "player": row["player"],
            "brefId": row["bref_id"],
            "year": row["year"],
            "age": round(float(row["age_at_signing"]), 2),
            "vetMinSalary": round(float(row["salary"])),
            "outcome": result,
            "draftPick": draft.get(row["bref_id"]),
        })

if checked != len(known):
    sys.exit(f"Only found {checked} of the {len(known)} signings in prove_it.json")

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["player", "brefId", "year", "age", "vetMinSalary", "outcome", "draftPick"])
    w.writeheader()
    w.writerows(extras)

print("matched prove_it.json on", checked, "signings")
print("extra signings:", len(extras))
