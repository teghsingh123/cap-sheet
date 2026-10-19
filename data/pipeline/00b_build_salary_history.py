"""
Fills in the gaps in the salary data and writes ../source/salary_history.csv,
the file every later step reads.

The original salary file (kept as salary_history_original.csv) was missing
some team-seasons entirely -- mostly players who were waived, stretched, or
hurt and barely played for a team that still paid them. Dragan Bender's
2019-20 minimum deal with Milwaukee (waived in February) is the case that
exposed it: without it, he dropped out of the vet-min list even though he
belongs at the top of it.

Basketball-Reference player pages (scraped by 00_scrape_player_salaries.py)
list every team that paid a player in a season. But they have their own gaps
(some two-way and short deals), and their amounts are sometimes cap figures
rather than what was paid. So this keeps every original row as-is and only
ADDS team-seasons the original file doesn't have.

Team codes are mapped to current franchise codes (PHO -> PHX, NJN -> BKN,
SEA -> OKC, ...) to match the original file, so a franchise moving or
renaming doesn't look like a player changing teams.
"""
import csv, json, os, shutil

LAST_YEAR = 2024  # keep the same 1991-2024 window as the original file

TEAM_MAP = {
    "PHO": "PHX", "NJN": "BKN", "BRK": "BKN", "SEA": "OKC", "VAN": "MEM",
    "WSB": "WAS", "CHH": "CHA", "CHO": "CHA", "NOH": "NOP", "NOK": "NOP",
}
FIELDS = ["player", "salary", "team", "year", "url", "bref_id"]

if not os.path.exists("../source/salary_history_original.csv"):
    shutil.copy("../source/salary_history.csv", "../source/salary_history_original.csv")

rows = []
have = set()  # (bref_id, year, team) already in the original file
with open("../source/salary_history_original.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append({k: r[k] for k in FIELDS})
        have.add((r["bref_id"], int(r["year"]), r["team"]))
names = {r["bref_id"]: r["player"] for r in rows}

added = []
scraped = 0
with open("../scrape/player_salaries.jsonl", encoding="utf-8") as f:
    for line in f:
        rec = json.loads(line)
        scraped += 1
        bref_id = rec["bref_id"]
        for s in rec["salaries"]:
            team = TEAM_MAP.get(s["team"], s["team"])
            if s["lg"] != "NBA" or not (1991 <= s["year"] <= LAST_YEAR) or s["salary"] <= 0:
                continue
            if (bref_id, s["year"], team) in have:
                continue
            have.add((bref_id, s["year"], team))
            added.append({
                "player": names.get(bref_id, rec["player"]),
                "salary": float(s["salary"]),
                "team": team,
                "year": s["year"],
                "url": f"https://www.basketball-reference.com/players/{bref_id[0]}/{bref_id}.html",
                "bref_id": bref_id,
            })

rows += added
for r in rows:
    r["salary"], r["year"] = float(r["salary"]), int(r["year"])
rows.sort(key=lambda r: (r["year"], r["team"], r["salary"]))
with open("../source/salary_history.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)

with open("../processed/added_salary_rows.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(sorted(added, key=lambda r: (r["player"], r["year"])))

print("players scraped so far:", scraped)
print("original rows:", len(rows) - len(added))
print("team-seasons added from Basketball-Reference:", len(added))
print("total rows:", len(rows))
