"""
Box-score and role stats for the vet-min model, one row per player per season.

Reads each season's per-game page plus the advanced page scrape_season_stats.py
already saved, and writes box_stats.csv. prev_season is the year that season
ended, the same as season_stats.csv, so 08_build_dataset.py can merge it on
brefId + prev_season. Run scrape_season_stats.py first.

Kept apart from season_stats.csv so the two-seasons-back merge in
08_build_dataset.py doesn't change.

A stat can be blank: a player with no shots has no true shooting. Those stay
blank here, for 08_build_dataset.py to fill.

Pages are saved in data/scrape/vet-min-model/per_game_html/, so reruns don't
download them again. Waits 4s between requests (robots.txt asks for 3).
"""
import csv, re, time, urllib.request
from pathlib import Path

HERE = Path(__file__).parent
PROCESSED = HERE / "../../../processed/vet-min-model"
SCRAPE = HERE / "../../../scrape/vet-min-model"
PER_GAME_DIR = SCRAPE / "per_game_html"
ADVANCED_DIR = SCRAPE / "season_stats_html"
OUT = PROCESSED / "box_stats.csv"
YEARS = range(1995, 2023)
DELAY = 4.0

PER_GAME = {"prev_ppg": "pts_per_g", "prev_rpg": "trb_per_g", "prev_apg": "ast_per_g",
            "prev_spg": "stl_per_g", "prev_bpg": "blk_per_g", "prev_tov": "tov_per_g"}
ADVANCED = {"prev_ts": "ts_pct", "prev_3pa_rate": "fg3a_per_fga_pct", "prev_usg": "usg_pct",
            "prev_ws48": "ws_per_48", "prev_obpm": "obpm", "prev_dbpm": "dbpm", "prev_vorp": "vorp"}

player_re = re.compile(r'data-stat="name_display"[^>]*data-append-csv="([a-z0-9]+)"|'
                       r'data-append-csv="([a-z0-9]+)"[^>]*data-stat="name_display"')
href_re = re.compile(r'data-stat="name_display"[^>]*>\s*<a href="/players/./([a-z0-9]+)\.html')
team_re = re.compile(r'data-stat="team_name_abbr"[^>]*>(?:<a[^>]*>)?([A-Z0-9]+)')
total_team_re = re.compile(r"^(TOT|\dTM)$")


def stat(row, name):
    match = re.search(rf'data-stat="{name}"[^>]*>(?:<strong>)?([^<]*)', row)
    return match.group(1).strip() if match else ""


def number(text):
    return float(text) if text else ""


def download(year):
    path = PER_GAME_DIR / f"per_game_{year}.html"
    if path.exists():
        return path
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_per_game.html"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cap-sheet research scraper)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        path.write_bytes(r.read())
    print("downloaded", year)
    time.sleep(DELAY)
    return path


def player_rows(path, table_id):
    """One row per player. A traded player has a row per team plus a combined
    row, and the combined one is used. Only the regular-season table is read."""
    html = path.read_text(encoding="utf-8", errors="replace")
    table = html.split(f'id="{table_id}"', 1)[1].split("</table>", 1)[0]

    players = {}
    for row in table.split("<tr")[1:]:
        player = player_re.search(row) or href_re.search(row)
        team = team_re.search(row)
        if player and team:
            bref_id = next(g for g in player.groups() if g)
            players.setdefault(bref_id, []).append((team.group(1), row))

    rows = {}
    for bref_id, stints in players.items():
        totals = [row for team, row in stints if total_team_re.match(team)]
        if len(stints) > 1 and len(totals) != 1:
            raise ValueError(f"{path.name} {bref_id}: {len(stints)} rows without one combined row")
        rows[bref_id] = totals[0] if totals else stints[0][1]
    return rows


PER_GAME_DIR.mkdir(exist_ok=True)
all_rows = []
for year in YEARS:
    per_game = player_rows(download(year), "per_game_stats")
    advanced = player_rows(ADVANCED_DIR / f"advanced_{year}.html", "advanced")
    for bref_id in per_game.keys() & advanced.keys():
        pg, adv = per_game[bref_id], advanced[bref_id]
        games = number(stat(pg, "games"))
        starts = number(stat(pg, "games_started"))
        all_rows.append({
            "brefId": bref_id,
            "prev_season": year,
            **{name: number(stat(pg, col)) for name, col in PER_GAME.items()},
            "prev_start_pct": round(starts / games, 3) if games and starts != "" else "",
            **{name: number(stat(adv, col)) for name, col in ADVANCED.items()},
        })
    print(year, "players:", len(per_game), "matched:", len(per_game.keys() & advanced.keys()))

all_rows.sort(key=lambda r: (r["prev_season"], r["brefId"]))
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(all_rows[0]))
    w.writeheader()
    w.writerows(all_rows)

print("rows:", len(all_rows))
