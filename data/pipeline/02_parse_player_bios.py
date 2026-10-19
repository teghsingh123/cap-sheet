import re, glob, csv

rows = []
row_re = re.compile(
    r'data-append-csv="([^"]+)"[^>]*>.*?</th>'
    r'<td class="right " data-stat="year_min" >(\d+)</td>'
    r'<td class="right " data-stat="year_max" >(\d+)</td>'
    r'<td class="center " data-stat="pos" >([^<]*)</td>'
    r'<td class="right " data-stat="height"[^>]*>([^<]*)</td>'
    r'<td class="right " data-stat="weight" >([^<]*)</td>'
    r'<td class="left " data-stat="birth_date" csk="(\d{8})"',
    re.S,
)

for path in sorted(glob.glob("../scrape/player_bio_html/bref_?.html")):
    html = open(path, encoding="utf-8").read()
    for m in row_re.finditer(html):
        bref_id, year_min, year_max, pos, height, weight, birth = m.groups()
        rows.append({
            "bref_id": bref_id, "year_min": year_min, "year_max": year_max,
            "pos": pos, "height": height, "weight": weight,
            "birth_date": f"{birth[:4]}-{birth[4:6]}-{birth[6:]}",
        })

with open("../processed/player_bios.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["bref_id", "year_min", "year_max", "pos", "height", "weight", "birth_date"])
    w.writeheader()
    w.writerows(rows)

print("total bio rows:", len(rows))
print("unique bref_id:", len(set(r["bref_id"] for r in rows)))
