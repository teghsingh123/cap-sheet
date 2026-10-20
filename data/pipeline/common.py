"""
Shared data and rules for the pipeline scripts that work with contracts
(04_build_vetmin_signings.py and the per-post scripts). Importing this loads
the processed files once; the functions answer the questions every script
needs answered the same way:

  - new_contract_team(): is this salary row a new contract, and for which team?
  - signing_date() / age_at_signing(): when, and how old was he?
  - is_dead_money_echo(): is a salary row just old money still being paid out?

Paths are relative to this file, so scripts can import it from any folder:

    sys.path.insert(0, "<path to data/pipeline>")
    import common
"""
import csv, datetime, os

DATA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _read(path):
    with open(os.path.join(DATA, path), encoding="utf-8") as f:
        return list(csv.DictReader(f))

# --- bio: true debut year + birthdate ---
bio = {r["bref_id"]: r for r in _read("processed/player_bios.csv")}

# --- draft position (undrafted players aren't in it: use draft.get) ---
draft = {r["bref_id"]: int(r["pick"]) for r in _read("processed/draft_picks.csv")}

# --- min salary scale, keyed (season end year, years of service) ---
min_scale = {}
for r in _read("processed/salary_min_scale.csv"):
    start, _ = r["season"].split("-")
    min_scale[(int(start) + 1, int(r["years_of_service"]))] = int(r["min_salary"])

# --- all salary rows, grouped by player and sorted by year ---
by_player = {}
for r in _read("source/salary_history.csv"):
    by_player.setdefault(r["bref_id"], []).append(r)
for rows in by_player.values():
    rows.sort(key=lambda r: int(r["year"]))

# --- transactions (from 00d_parse_transactions.py), to tell how a player
#     got to a team: signed, or brought over on an existing contract ---
# Basketball-Reference uses the team code from the time (SEA, NJN...); the
# salary data uses the franchise's current code.
TEAM_CODES = {"BRK": "BKN", "NJN": "BKN", "PHO": "PHX", "CHH": "CHA", "CHO": "CHA",
              "NOH": "NOP", "NOK": "NOP", "SEA": "OKC", "VAN": "MEM", "WSB": "WAS"}
transactions = {}
contract_events = {}  # bref_id -> [(date, team, "two-way" | "regular")], for the two-way check
for r in _read("processed/transactions.csv"):
    if r["type"] in ("signed", "traded", "claimed", "expansion"):
        transactions.setdefault(r["bref_id"], []).append(r)
    if r["type"] == "signed" and r["to_team"]:
        kind = "two-way" if "two-way contract" in r["detail"] else "regular"
        contract_events.setdefault(r["bref_id"], []).append((r["date"], r["to_team"], kind))
    elif r["type"] == "converted":  # "converted X from a two-way contract to a regular contract"
        contract_events.setdefault(r["bref_id"], []).append((r["date"], r["from_team"], "regular"))

def _team(code):
    return TEAM_CODES.get(code, code)

def _window(year):
    """The `year` season, June through June. Transactions are matched by date,
    not by which season's page the log filed them on -- late-June trades and
    early-July signings land on either side inconsistently."""
    return f"{year - 1}-06-01", f"{year}-06-30"

def arrivals_by_team(bref_id, year, team):
    """Ways the player joined `team` during the `year` season."""
    start, end = _window(year)
    return {
        t["type"] for t in transactions.get(bref_id, [])
        if start <= t["date"] <= end and _team(t["to_team"]) == team
    }

def signed_before_trade(bref_id, year, team, salary_teams):
    """The team that signed the player earlier in the `year` season, up to the
    day he was traded/claimed to `team`, if that team has no salary row of its
    own that season (so its contract must be the one credited to `team`).
    Returns (that team, True if it signed him the same day it traded him --
    a sign-and-trade), or (None, False)."""
    start, end = _window(year)
    moves = [t for t in transactions.get(bref_id, []) if start <= t["date"] <= end]
    arrived = min(t["date"] for t in moves if _team(t["to_team"]) == team)
    origins = [
        t for t in moves
        if t["type"] == "signed" and t["date"] <= arrived and t["to_team"]
        and _team(t["to_team"]) not in salary_teams
    ]
    if not origins:
        return None, False
    return _team(origins[-1]["to_team"]), origins[-1]["date"] == arrived

def ended_on_two_way(bref_id, year, team):
    """True if the last contract `team` gave the player during the `year` season
    was a two-way. Uses the last one because players move between deals in a
    season: Marquese Chriss signed a regular deal with GSW in Sept 2019, went to
    a two-way in January and was converted back to regular in February (not a
    two-way); Daishen Nix signed an Exhibit 10 with MIN, then a two-way (two-way)."""
    start, end = _window(year)
    events = sorted(
        (d, kind) for d, t, kind in contract_events.get(bref_id, [])
        if start <= d <= end and _team(t) == team
    )
    return bool(events) and events[-1][1] == "two-way"

def re_signed(bref_id, year, team):
    """True if `team` signed the player to a new standard deal during the
    `year` season (not a two-way, not an extension of the deal he had)."""
    start, end = _window(year)
    return any(
        t["type"] == "signed" and start <= t["date"] <= end and _team(t["to_team"]) == team
        and "two-way" not in t["detail"] and "extension" not in t["detail"]
        for t in transactions.get(bref_id, [])
    )

def signing_date(bref_id, year, team):
    """Earliest date `team` signed the player during the `year` season, or None."""
    start, end = _window(year)
    dates = [
        t["date"] for t in transactions.get(bref_id, [])
        if t["type"] == "signed" and start <= t["date"] <= end and _team(t["to_team"]) == team
    ]
    return min(dates, default=None)

def age_at_signing(bref_id, year, team):
    """Age on the day he signed, from the transactions log; Oct 1 of the season
    if the log has no date (Bender signed July 26, 2019: 21.69, not the 21.87
    he'd be by Oct 1)."""
    birth = datetime.date.fromisoformat(bio[bref_id]["birth_date"])
    signed_on = signing_date(bref_id, year, team)
    on = datetime.date.fromisoformat(signed_on) if signed_on else datetime.date(year - 1, 10, 1)
    return (on - birth).days / 365.25

def new_contract_team(bref_id, year, row_team, teams_by_year):
    """Is the player's `year` salary row with `row_team` a new contract?
    Returns (team that signed it, None) if so, else (None, reason).

    - Same team as last season usually means a later year of the same deal --
      unless the log shows the team signed him again that season: Indiana
      re-signed Lavoy Allen to a 1-year, $948,163 minimum in July 2014 after
      paying him $3.1M the year before.
    - A team change alone doesn't mean a new contract: a player traded,
      claimed off waivers or taken in an expansion draft brings his old deal
      with him (Pachulia to MIL in 2004, Middleton to MIL in 2013, Rollins to
      WAS in 2023). If the log has no arrival at all, the row is kept: the log
      isn't complete, and it sometimes records a waiver claim as "signed"
      (Jeremy Lin to NYK, 2011), which also keeps the row.
    - But the salary data credits a contract traded mid-season to the team
      holding it at the end, often with no row at all for the team that signed
      it. Nik Stauskas signed a 1-year minimum with Portland in July 2018; the
      full $1,621,415 sits on Indiana's row (traded POR -> CLE -> HOU -> IND,
      then waived). So if a team with no salary row that season signed him
      before he was traded here, it's that team's new contract.
    - A sign-and-trade is a new contract for the team he was traded to: the
      old team signs him the day it trades him (New Orleans signed Lonzo Ball
      and traded him to Chicago on Aug 8, 2021).
    - Two-way contracts are a separate contract type paying a flat amount
      (half the rookie minimum since 2023 -- Theo Maledon's $559,782 with
      Charlotte), not a standard deal.
    """
    prev_teams = teams_by_year.get(year - 1)
    if prev_teams is not None and row_team in prev_teams and not re_signed(bref_id, year, row_team):
        return None, "same_stint"
    team = row_team
    arrivals = arrivals_by_team(bref_id, year, team)
    if arrivals and "signed" not in arrivals:
        origin, sign_and_trade = signed_before_trade(bref_id, year, team, teams_by_year[year])
        if sign_and_trade:
            pass  # new contract, with the team he was traded to
        elif origin is None or (prev_teams is not None and origin in prev_teams):
            return None, "carried"
        else:
            team = origin
    if ended_on_two_way(bref_id, year, team):
        return None, "two_way"
    return team, None

# A (team, salary) pair that closely matches one from an EARLIER season for
# the same player is almost certainly stretched dead money still being paid
# out (DeAndre Jordan's ~$7.9M Detroit cap hit in 2022 shows up again, barely
# changed, in 2023 though he was never on Detroit's roster that year), not a
# fresh salary. Only counts if that earlier season also shows the player with
# ANOTHER team at the same time -- the signature of a trade-then-cut churn
# year, as opposed to a player staying on one team on a flat-ish salary --
# AND the salary itself is clearly above minimum level, since back-to-back
# minimum re-signings with the same team (rising ~5-10%/year on the scale)
# would otherwise get misflagged whenever an unrelated dead-money row from a
# different team exists that season (Jordan's 2023->2024 Denver re-signing).
def looks_like_min_level(bref_id, year, salary):
    b = bio.get(bref_id)
    if not b:
        return False
    yos = max(0, min(year - int(b["year_min"]), 10))
    min_sal = min_scale.get((year, yos))
    return min_sal is not None and salary / min_sal <= 1.15

def is_dead_money_echo(bref_id, player_rows, team, salary, before_year, tol=0.15):
    if looks_like_min_level(bref_id, before_year, salary):
        return False
    for r in player_rows:
        ry = int(r["year"])
        if ry < before_year and r["team"] == team:
            rs = float(r["salary"])
            if rs > 0 and abs(salary - rs) / rs < tol:
                other_teams = {rr["team"] for rr in player_rows if int(rr["year"]) == ry} - {team}
                if other_teams:
                    return True
    return False

# Minimum salary is a legal floor for a *full* season. A player signed
# mid-season (waiver pickup, post-buyout, 10-day-turned-rest-of-season) gets
# that same minimum rate prorated for the games left, so his total pay can
# land well below the full-season number while still being a genuine minimum
# signing. So allow anything from a small floor (filters out emergency
# call-ups) up to just above the full number.
RATIO_MAX = 1.03
RATIO_MIN = 0.22  # ~1/4 season minimum; below this it's an emergency/cup-of-coffee deal, not a real signing
