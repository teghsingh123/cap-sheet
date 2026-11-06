"""
Fills a gap in the draft data for the vet-min model.

data/processed/draft_picks.csv starts with the 1990 draft, so a player drafted
earlier has a blank draftPick in prove_it.json and looks undrafted (Shawn Kemp,
#17 in 1989, for example).

This downloads the 1970-1989 draft pages and writes old_draft_picks.csv, with
only the players who are in prove_it.json or extra_signings.csv and have a
blank draftPick. Run build_extra_signings.py first.

It uses its own folder on purpose: the shared pipeline reads
data/scrape/draft_html/, so saving these pages there would change the site's
data the next time the pipeline runs.

Pages are saved in data/scrape/vet-min-model/old_draft_html/, so reruns don't download them again.
Waits 4s between requests (robots.txt asks for 3).
"""
import csv, json, re, time, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
PROCESSED = HERE / "../../../processed/vet-min-model"
HTML_DIR = HERE / "../../../scrape/vet-min-model/old_draft_html"
PROVE_IT = HERE / "../../../../web/public/data/kuminga-line/prove_it.json"
OUT = PROCESSED / "old_draft_picks.csv"
YEARS = range(1970, 1990)
DELAY = 4.0

pick_re = re.compile(r'data-stat="pick_overall"[^>]*csk="(\d+)"')
player_re = re.compile(r'data-stat="player"[^>]*>\s*<a href=[\'"]/players/./([a-z0-9]+)\.html')


def download(year):
    path = HTML_DIR / f"draft_{year}.html"
    if path.exists():
        return path
    url = f"https://www.basketball-reference.com/draft/NBA_{year}.html"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cap-sheet research scraper)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        path.write_bytes(r.read())
    print("downloaded", year)
    time.sleep(DELAY)
    return path


def parse(path):
    """Reads one row at a time, so a pick who never played can't shift the
    pick number onto the next player."""
    html = path.read_text(encoding="utf-8", errors="replace")
    picks = []
    for row in html.split("<tr")[1:]:
        pick = pick_re.search(row)
        player = player_re.search(row)
        if pick and player:
            picks.append((int(pick.group(1)), player.group(1)))
    return picks


HTML_DIR.mkdir(exist_ok=True)
signings = json.loads(PROVE_IT.read_text(encoding="utf-8"))["signings"]
blank_ids = {s["brefId"] for s in signings if s["draftPick"] is None}
with open(PROCESSED / "extra_signings.csv", encoding="utf-8") as f:
    blank_ids |= {r["brefId"] for r in csv.DictReader(f) if not r["draftPick"]}

rows = {}
for year in YEARS:
    picks = parse(download(year))
    print(year, "picks with a player page:", len(picks))
    for pick, bref_id in picks:
        if bref_id in blank_ids:
            # keep the latest pick if a player was drafted twice: it's the one
            # that took him to the NBA
            rows[bref_id] = {"draft_year": year, "pick": pick, "brefId": bref_id}

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["draft_year", "pick", "brefId"])
    w.writeheader()
    w.writerows(rows.values())

print("blank players:", len(blank_ids), "found in old drafts:", len(rows))
