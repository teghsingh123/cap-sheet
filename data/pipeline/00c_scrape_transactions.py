"""
Downloads Basketball-Reference's league transactions page for every season
from 1990-91 through 2023-24 and saves the raw HTML to
../scrape/transactions_html/transactions_<year>.html (year = season end).

Why: salary rows alone can't tell a new signing from a player whose old
contract moved with him in a trade, waiver claim or expansion draft (e.g.
Ryan Rollins, traded GSW -> WAS in 2023 on his rookie deal). The
transactions log says which one it was.

Resumable: seasons already saved are skipped. Waits 4s between requests
(robots.txt asks for 3).
"""
import os, time, urllib.request, urllib.error

OUT_DIR = "../scrape/transactions_html"
YEARS = range(1991, 2025)
DELAY = 4.0

def fetch(year):
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}_transactions.html"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (cap-sheet research scraper)"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 429:  # rate limited -- back off hard
                time.sleep(60 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError:
            time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"gave up on {url}")

os.makedirs(OUT_DIR, exist_ok=True)
for year in YEARS:
    path = f"{OUT_DIR}/transactions_{year}.html"
    if os.path.exists(path):
        continue
    html = fetch(year)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(year, f"{len(html):,} bytes")
    time.sleep(DELAY)
