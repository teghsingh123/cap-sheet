import re, glob, csv

rows = []
for path in glob.glob("../scrape/salary_scale_html/minscale_*.html"):
    html = open(path, encoding="utf-8").read()

    if 'Minimum Annual Salary for Contracts signed during the' in html:
        # format A: per-season h3 sub-tables, columns = Year 1..Year 5 of the contract
        sections = re.split(r'<h3>Minimum Annual Salary for Contracts signed during the ([\d\-]+) Season</h3>', html)
        for i in range(1, len(sections), 2):
            season = sections[i]
            content = sections[i+1]
            table_end = content.find('</table>')
            table_html = content[:table_end]
            for row_m in re.finditer(r'<tr><td data-th="YOS" rel="-(\d+)">.*?</td>(.*?)</tr>', table_html, re.S):
                yos = int(row_m.group(1))
                rest = row_m.group(2)
                year1_m = re.search(r'<td data-th="Year 1" rel="(\d*)"', rest)
                if year1_m and year1_m.group(1):
                    rows.append((season, yos, int(year1_m.group(1))))
    else:
        # format B: single wide table, columns = season, one row per YOS
        head_m = re.search(r'<thead>(.*?)</thead>', html, re.S)
        seasons = re.findall(r'scope="col">([\d\-]+)</td>', head_m.group(1))
        body_m = re.search(r'<tbody>(.*?)</tbody>', html, re.S)
        for row_m in re.finditer(r'<tr>\s*<td data-th="YOS" rel="-?(\d+)">.*?</td>(.*?)</tr>', body_m.group(1), re.S):
            yos = int(row_m.group(1))
            cells = re.findall(r'rel="(\d*)"', row_m.group(2))
            for season, val in zip(seasons, cells):
                if val and val != '0':
                    rows.append((season, yos, int(val)))

rows = sorted(set(rows), key=lambda r: (r[0], r[1]))
with open("../processed/salary_min_scale.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["season", "years_of_service", "min_salary"])
    w.writerows(rows)

print("total rows", len(rows))
seasons = sorted(set(r[0] for r in rows))
print("seasons covered:", len(seasons))
print(seasons)
