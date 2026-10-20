"""
Parses the season transaction pages saved by 00c_scrape_transactions.py into
../processed/transactions.csv, one row per player per transaction:

  season, date, bref_id, player, type, from_team, to_team, detail

type is one of: signed, waived, released, traded, claimed, expansion,
converted, sold, assigned, recalled, other. Team codes are
Basketball-Reference's from the time (BRK, SEA, CHH...), which don't always
match the current franchise codes in salary_history.csv -- 04 maps them. Match
on date, not season: late-June trades and early-July signings get filed on
either side of the season line inconsistently.

Trades are split into one row per player with the direction each player
moved. Multi-team trades are written as "In a 3-team trade, the A traded x
to the B; the B traded y to the C; ..." so each ";" clause is parsed on its
own. In a two-team trade, players after "for" went the other way.
Players named only as future draft-pick results ("(Javon Small was later
selected)") didn't move in the trade and are dropped.
"""
import csv, datetime, glob, html, re

TEAM_FROM = re.compile(r'<a data-attr-from="([A-Z]{3})"')
TEAM_TO = re.compile(r'<a data-attr-to="([A-Z]{3})"')
PLAYER = re.compile(r'<a href="/players/[a-z]/([a-z0-9]+)\.html">([^<]+)</a>')
LATER_SELECTED = re.compile(r'\([^()]*was later selected\)')
TYPES = [
    ("traded", "traded"), ("claimed", "claimed"), ("expansion draft", "expansion"),
    ("converted", "converted"), ("signed", "signed"), ("waived", "waived"),
    ("released", "released"), ("sold", "sold"), ("assigned", "assigned"),
    ("recalled", "recalled"),
]

def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()

def players(s):
    return PLAYER.findall(LATER_SELECTED.sub("", s))

def parse_trade_clause(clause):
    """-> [(bref_id, name, from_team, to_team)] for one 'A traded x to the B [for y]' clause"""
    f, t = TEAM_FROM.search(clause), TEAM_TO.search(clause)
    if not (f and t):
        return []
    sent, _, rest = clause.partition(t.group(0))
    out = [(b, n, f.group(1), t.group(1)) for b, n in players(sent)]
    if " for " in rest:
        back = rest.split(" for ", 1)[1]
        out += [(b, n, t.group(1), f.group(1)) for b, n in players(back)]
    return out

def parse(p_html):
    """-> (type, [(bref_id, name, from_team, to_team)]) for one transaction <p>"""
    text = plain(p_html)
    kind = next((k for word, k in TYPES if word in text), "other")
    if kind == "traded":
        moves = []
        for clause in p_html.split(";"):
            moves += parse_trade_clause(clause)
        return kind, moves
    f, t = TEAM_FROM.search(p_html), TEAM_TO.search(p_html)
    from_team = f.group(1) if f else ""
    to_team = t.group(1) if t else ""
    if kind == "expansion":
        # "The X drafted P from the Y in the NBA expansion draft" -- Y is
        # sometimes a plain link with no data-attr, so fall back to href
        m = re.search(r'from the <a [^>]*href="/teams/([A-Z]{3})/', p_html)
        from_team = m.group(1) if m else from_team
    if kind == "claimed":
        m = re.search(r'on waivers from the <a [^>]*href="/teams/([A-Z]{3})/', p_html)
        from_team = m.group(1) if m else from_team
    return kind, [(b, n, from_team, to_team) for b, n in players(p_html)]

rows = []
for path in sorted(glob.glob("../scrape/transactions_html/transactions_*.html")):
    season = int(re.search(r"(\d{4})\.html$", path).group(1)) #type: ignore
    with open(path, encoding="utf-8") as f:
        page = f.read()
    for date_str, body in re.findall(r"<li><span>([^<]+)</span>(.*?)</li>", page, re.S):
        try:
            date = datetime.datetime.strptime(date_str.strip(), "%B %d, %Y").date().isoformat()
        except ValueError:
            continue  # not a transaction list item
        for p in re.findall(r"<p>(.*?)</p>", body, re.S):
            kind, moves = parse(p)
            detail = plain(p)
            for bref_id, name, from_team, to_team in moves:
                rows.append({
                    "season": season, "date": date, "bref_id": bref_id,
                    "player": html.unescape(name), "type": kind,
                    "from_team": from_team, "to_team": to_team, "detail": detail,
                })

with open("../processed/transactions.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["season", "date", "bref_id", "player", "type", "from_team", "to_team", "detail"])
    w.writeheader()
    w.writerows(rows)

counts = {}
for r in rows:
    counts[r["type"]] = counts.get(r["type"], 0) + 1
print("transaction rows:", len(rows), "players:", len({r["bref_id"] for r in rows}))
print(dict(sorted(counts.items(), key=lambda kv: -kv[1])))
