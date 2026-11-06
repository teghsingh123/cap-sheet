"""
Finds the date each minimum signing happened, for the V6 timing feature.

Dates come from the shared transactions data, using the same signing_date() rule
as the rest of the site. A date is known on signing day, so it's safe to use as
a feature. ratioOfMin looks similar but isn't: a player waived early has a smaller
recorded salary, so it can reflect what happened after he signed.

Writes signing_dates.csv, which 08_build_dataset.py can merge on brefId + year +
vetMinSalary. A signing with no matching transaction is left out, so it shows up
as a blank after the merge.
"""
import csv, json, sys
from pathlib import Path

HERE = Path(__file__).parent
PROCESSED = HERE / "../../../processed/vet-min-model"
sys.path.insert(0, str(HERE / "../../../pipeline"))
from common import signing_date

ALL_SIGNINGS = HERE / "../../../../web/public/data/kuminga-line/all_signings.json"
OUT = PROCESSED / "signing_dates.csv"

signings = json.loads(ALL_SIGNINGS.read_text(encoding="utf-8"))["signings"]

rows = []
for s in signings:
    date = signing_date(s["brefId"], s["year"], s["team"])
    if date:
        rows.append({
            "brefId": s["brefId"],
            "year": s["year"],
            "vetMinSalary": s["salary"],
            "signing_date": date,
        })

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["brefId", "year", "vetMinSalary", "signing_date"])
    w.writeheader()
    w.writerows(rows)

print("signings:", len(signings), "with a date:", len(rows))
