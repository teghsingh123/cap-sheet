"""
Exports the current-season veteran-minimum-by-years-of-service table for the
MinScaleTable component on the site. This formalizes a step that used to be
a one-off `python -c` command run by hand -- rerun this whenever the season
in SEASON changes.
"""
import csv, json

SEASON = "2025-2026"  # matches the "season" column format in salary_min_scale.csv

rows = [r for r in csv.DictReader(open("../processed/salary_min_scale.csv")) if r["season"] == SEASON]
rows.sort(key=lambda r: int(r["years_of_service"]))

scale = [{"yos": int(r["years_of_service"]), "minSalary": int(float(r["min_salary"]))} for r in rows]

start, end = SEASON.split("-")
display_season = f"{start}-{end[2:]}"  # "2025-2026" -> "2025-26"
with open("../../web/public/data/min_scale.json", "w", encoding="utf-8") as f:
    json.dump({"season": display_season, "scale": scale}, f, indent=2)

print("wrote", len(scale), "rows for season", display_season)
