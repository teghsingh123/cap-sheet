import csv

draft = {}
with open("draft_picks.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        draft[row["bref_id"]] = int(row["pick"])

with open("kuminga_comps.csv", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

for r in rows:
    r["draft_pick"] = draft.get(r["bref_id"], "")

fieldnames = list(rows[0].keys())
with open("kuminga_comps_with_draft.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    w.writerows(rows)

with_pick = [r for r in rows if r["draft_pick"] != ""]
with_pick.sort(key=lambda r: int(r["draft_pick"]))
print(f"{len(with_pick)}/{len(rows)} comps matched to a draft pick")
print()
print("Highest-drafted players in the comp list (biggest pedigree, still fell to vet min young):")
for r in with_pick[:15]:
    print(f"pick #{r['draft_pick']:>3}  age {float(r['age_at_signing']):5.2f}  {r['player']:22s} {r['year']}  {r['drop_pct']}% drop")
