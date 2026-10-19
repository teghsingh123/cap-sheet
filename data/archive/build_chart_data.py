"""
Final step of the data pipeline: turn the CSV outputs into a single trimmed
JSON the frontend chart can load directly. No more analysis happens here —
this just reshapes and renames fields for the chart's sake.

Output: chart_data.json
  - "cliffs": every new-signing vet-min row with a known prior-season salary
    drop (any age, any drop size) -- this is the "full history" view.
  - each row also carries `isKumingaComp` (age < 27 and drop > 50%) so the
    frontend can filter/zoom into that cluster without a second dataset.
"""
import csv, json

draft = {}
with open("draft_picks.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        draft[row["bref_id"]] = int(row["pick"])

cliffs = []
with open("vet_min_flagged_v2.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if not row["drop_pct"]:
            continue
        drop_pct = float(row["drop_pct"])
        if drop_pct <= 0:
            continue  # only real cliffs, not raises
        age = float(row["age_at_signing"])
        cliffs.append({
            "player": row["player"],
            "brefId": row["bref_id"],
            "year": int(row["year"]),
            "age": round(age, 2),
            "yearsOfService": int(row["true_yos"]),
            "prevSalary": round(float(row["prev_salary"])),
            "salary": round(float(row["salary"])),
            "dropPct": drop_pct,
            "ratioOfMin": float(row["ratio"]),
            "team": row["team"],
            "draftPick": draft.get(row["bref_id"]),  # null if undrafted/unmatched (pre-1990 or 2022+ draft)
            "isKumingaComp": age < 27 and drop_pct > 50,
        })

cliffs.sort(key=lambda r: r["age"])

with open("chart_data.json", "w", encoding="utf-8") as f:
    json.dump({"cliffs": cliffs}, f, indent=2)

print("total cliff rows:", len(cliffs))
print("flagged as Kuminga comps:", sum(1 for c in cliffs if c["isKumingaComp"]))
print("with a matched draft pick:", sum(1 for c in cliffs if c["draftPick"] is not None))
print()
print("sample record:")
print(json.dumps(cliffs[0], indent=2))
