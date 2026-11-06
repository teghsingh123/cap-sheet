"""
Regular-season stats for the vet-min model, one row per player per season.

Downloads Basketball-Reference's advanced stats page for each season the model
looks back on and writes season_stats.csv. prev_season is the year that season
ended (2015 = 2014-15). 08_build_dataset.py joins on it with signing year - 1,
so a player's stats always come from the season before he signed.

Pages are saved in data/scrape/vet-min-model/season_stats_html/, so reruns don't download them again.
Waits 4s between requests (robots.txt asks for 3).
"""
import csv, re, time, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
PROCESSED = HERE / "../../../processed/vet-min-model"
HTML_DIR = HERE / "../../../scrape/vet-min-model/season_stats_html"
OUT = PROCESSED / "season_stats.csv"
YEARS = range(1995, 2023)
DELAY = 4.0

# Regular-season games per team. The 2019-20 season stopped early, so teams
# played 63 to 75 games; 72 is a rough middle, and the share is capped at 1.
SEASON_GAMES = {1999: 50, 2012: 66, 2020: 72, 2021: 72}

player_re = re.compile(r'data-stat="name_display"[^>]*data-append-csv="([a-z0-9]+)"|'
                       r'data-append-csv="([a-z0-9]+)"[^>]*data-stat="name_display"')
team_re = re.compile(r'data-stat="team_name_abbr"[^>]*>(?:<a[^>]*>)?([A-Z0-9]+)')
total_team_re = re.compile(r"^(TOT|\dTM)$")


def stat(row, name):
    match = re.search(rf'data-stat="{name}"[^>]*>(?:<strong>)?([^<]*)', row)
    return match.group(1).strip() if match else ""


def download(year):
    path = HTML_DIR / f"advanced_{year}.html"
    if path.exists():
        return path
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_advanced.html"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cap-sheet research scraper)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        path.write_bytes(r.read())
    print("downloaded", year)
    time.sleep(DELAY)
    return path


def parse(path, year):
    html = path.read_text(encoding="utf-8", errors="replace")
    # The page also has a playoffs table, which must not be counted.
    table = html.split('id="advanced"', 1)[1].split("</table>", 1)[0]

    players = {}
    for row in table.split("<tr")[1:]:
        player = player_re.search(row)
        team = team_re.search(row)
        games, minutes, bpm = stat(row, "games"), stat(row, "mp"), stat(row, "bpm")
        if not (player and team and games and minutes and bpm):
            continue
        bref_id = player.group(1) or player.group(2)
        players.setdefault(bref_id, []).append({
            "team": team.group(1), "games": int(games), "minutes": int(minutes), "bpm": float(bpm),
        })

    rows = []
    season_games = SEASON_GAMES.get(year, 82)
    for bref_id, stints in players.items():
        # A traded player has a row per team plus a combined row. Use the combined one.
        totals = [s for s in stints if total_team_re.match(s["team"])]
        if len(stints) > 1 and len(totals) != 1:
            raise ValueError(f"{year} {bref_id}: {len(stints)} rows without one combined row")
        s = totals[0] if totals else stints[0]
        rows.append({
            "brefId": bref_id,
            "prev_season": year,
            "prev_mpg": round(s["minutes"] / s["games"], 1),
            "prev_games_pct": round(min(s["games"] / season_games, 1), 3),
            "prev_bpm": s["bpm"],
        })
    return rows


HTML_DIR.mkdir(exist_ok=True)
all_rows = []
for year in YEARS:
    rows = parse(download(year), year)
    print(year, "players:", len(rows))
    all_rows += rows

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["brefId", "prev_season", "prev_mpg", "prev_games_pct", "prev_bpm"])
    w.writeheader()
    w.writerows(all_rows)

print("rows:", len(all_rows))
