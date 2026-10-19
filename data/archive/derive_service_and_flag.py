"""
Step 1: derive years-of-service (YOS) per player-season from their own salary history.
  - YOS is 0 in a player's first recorded season, 1 in the next, etc.
  - This mirrors the NBA's rule that YOS increments once per season played, not per calendar year,
    which is good enough for a first pass (misses partial-season rookie-year timing edge cases).

Step 2: join to min_salary_scale.csv on (season, YOS) and flag rows where salary ~= min.
"""
import csv

# --- load salary history ---
players = {}  # bref_id -> list of (year:int, row:dict)
with open("salary_backup.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        players.setdefault(row["bref_id"], []).append(row)

for bref_id, rows in players.items():
    rows.sort(key=lambda r: int(r["year"]))

# assign YOS
for bref_id, rows in players.items():
    first_year = int(rows[0]["year"])
    for row in rows:
        row["yos"] = int(row["year"]) - first_year

# --- load min salary scale ---
# season format there is "1995-1996", salary_backup year is the *ending* year (e.g. 1996 for 1995-96),
# based on cap.csv convention where "1995-1996" -> year 1996. Confirm this mapping before trusting it.
min_scale = {}  # (end_year, yos) -> min_salary
with open("min_salary_scale.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        start, end = row["season"].split("-")
        end_year = int(start) + 1  # "1995-1996" -> 1996
        min_scale[(end_year, int(row["years_of_service"]))] = int(row["min_salary"])

# --- flag vet-min seasons ---
TOLERANCE = 0.03  # 3% band to allow for prorated/rounding differences
flagged = []
for bref_id, rows in players.items():
    for row in rows:
        year = int(row["year"])
        yos = row["yos"]
        yos_capped = min(yos, 10)  # scale buckets 10+ years of service together
        salary = float(row["salary"])
        key = (year, yos_capped)
        if key not in min_scale:
            continue
        min_sal = min_scale[key]
        if min_sal == 0:
            continue
        ratio = salary / min_sal
        if abs(ratio - 1) <= TOLERANCE:
            flagged.append({
                "player": row["player"], "bref_id": bref_id, "year": year,
                "yos": yos, "salary": salary, "min_salary": min_sal, "team": row["team"],
            })

flagged.sort(key=lambda r: r["year"])
with open("vet_min_flagged.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["player", "bref_id", "year", "yos", "salary", "min_salary", "team"])
    w.writeheader()
    w.writerows(flagged)

print(f"players: {len(players)}")
print(f"flagged vet-min-ish rows: {len(flagged)}")
print(f"flagged with yos==0 (rookie min, NOT what we want): {sum(1 for r in flagged if r['yos']==0)}")
print(f"flagged with yos>=1 (actual vet min candidates): {sum(1 for r in flagged if r['yos']>=1)}")
