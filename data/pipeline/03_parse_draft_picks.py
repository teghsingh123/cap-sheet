import re, glob, csv

rows = []
row_re = re.compile(
    r'data-stat="pick_overall" csk="(\d+)"[^>]*>.*?</td>'
    r'.*?data-stat="player"[^>]*><a href=\'/players/./([a-z0-9]+)\.html\'',
    re.S,
)

for path in sorted(glob.glob("../scrape/draft_html/draft_*.html")):
    year = re.search(r"(\d{4})", path).group(1)
    html = open(path, encoding="utf-8").read()
    for m in row_re.finditer(html):
        pick, bref_id = m.groups()
        if not bref_id:
            continue
        rows.append({"draft_year": year, "pick": int(pick), "bref_id": bref_id})

with open("../processed/draft_picks.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["draft_year", "pick", "bref_id"])
    w.writeheader()
    w.writerows(rows)

print("total draft rows:", len(rows))
