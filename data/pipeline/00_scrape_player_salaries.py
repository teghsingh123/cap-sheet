"""
Scrapes the Salaries table from every Basketball-Reference player page for
players active in 1991 or later, and saves the rows to
../scrape/player_salaries.jsonl (one JSON object per player).

Why: the original salary_history.csv was missing some seasons entirely --
e.g. Dragan Bender's 2019-20 minimum deal with Milwaukee (waived in February)
never showed up, so he fell out of the vet-min list even though he's the
youngest former top-10 pick to sign one. Player pages list every team that
paid a player in a season, including teams that waived him.

Resumable: players already in the jsonl file are skipped, so it can be
stopped and restarted. Waits 4s between requests (robots.txt asks for 3).
"""
import csv, json, os, re, time, urllib.request, urllib.error

OUT = "../scrape/player_salaries.jsonl"
DELAY = 4.0

row_re = re.compile(
    r'data-stat="season" >(\d{4})-\d{2}</th>'
    r'<td class="left " data-stat="team_name" ><a href="/teams/([A-Z]{3})/\d{4}\.html">[^<]*</a></td>'
    r'<td class="left " data-stat="lg_id" >(?:<a [^>]*>)?([A-Z]+)(?:</a>)?</td>'
    r'<td class="right " data-stat="salary" csk="(\d+)"'
)

def player_ids():
    with open("../processed/player_bios.csv", encoding="utf-8") as f:
        ids = [r["bref_id"] for r in csv.DictReader(f) if int(r["year_max"]) >= 1991]
    # top-10 picks first: they decide the article's main answer, so they
    # should be done before everyone else
    with open("../processed/draft_picks.csv", encoding="utf-8") as f:
        top10 = {r["bref_id"] for r in csv.DictReader(f) if int(r["pick"]) <= 10}
    return sorted(ids, key=lambda p: p not in top10)

def fetch(bref_id):
    url = f"https://www.basketball-reference.com/players/{bref_id[0]}/{bref_id}.html"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cap-sheet research scraper)"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                return res.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 429:
                # rate limited: back off hard before retrying
                time.sleep(120 * (attempt + 1))
                continue
            time.sleep(10)
        except Exception:
            time.sleep(10)
    raise RuntimeError(f"giving up on {bref_id}")

def parse(html, bref_id):
    name = re.search(r"<h1>\s*<span>([^<]+)</span>", html)
    i = html.find('id="all_salaries"')
    rows = []
    if i != -1:
        table = html[i:html.find("</table>", i)]
        for season, team, lg, salary in row_re.findall(table):
            rows.append({"year": int(season) + 1, "team": team, "lg": lg, "salary": int(salary)})
    return {"bref_id": bref_id, "player": name.group(1).strip() if name else bref_id, "salaries": rows}

done = set()
if os.path.exists(OUT):
    with open(OUT, encoding="utf-8") as f:
        done = {json.loads(line)["bref_id"] for line in f if line.strip()}

todo = [p for p in player_ids() if p not in done]
print(f"{len(done)} already scraped, {len(todo)} to go", flush=True)

with open(OUT, "a", encoding="utf-8") as out:
    for n, bref_id in enumerate(todo, 1):
        html = fetch(bref_id)
        rec = parse(html, bref_id) if html else {"bref_id": bref_id, "player": bref_id, "salaries": [], "missing": True}
        out.write(json.dumps(rec) + "\n")
        out.flush()
        if n % 50 == 0:
            print(f"{n}/{len(todo)}", flush=True)
        time.sleep(DELAY)

print("done", flush=True)
