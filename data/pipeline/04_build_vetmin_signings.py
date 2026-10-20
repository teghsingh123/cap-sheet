import csv, datetime

# --- load bio: true debut year + birthdate ---
bio = {}
with open("../processed/player_bios.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        bio[row["bref_id"]] = row

# --- load min salary scale ---
min_scale = {}
with open("../processed/salary_min_scale.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        start, _ = row["season"].split("-")
        end_year = int(start) + 1
        min_scale[(end_year, int(row["years_of_service"]))] = int(row["min_salary"])

# --- load all salary rows, grouped by player, so we can tell a *new* contract
#     stint (team changed, or a gap year) from just another season of an
#     existing multi-year deal riding the minimum scale up ---
by_player = {}
with open("../source/salary_history.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        by_player.setdefault(row["bref_id"], []).append(row)

for bref_id, rows in by_player.items():
    rows.sort(key=lambda r: int(r["year"]))

# --- load transactions (from 00d_parse_transactions.py), to tell how a player
#     got to a team: signed, or brought over on an existing contract ---
# Basketball-Reference uses the team code from the time (SEA, NJN...); the
# salary data uses the franchise's current code.
TEAM_CODES = {"BRK": "BKN", "NJN": "BKN", "PHO": "PHX", "CHH": "CHA", "CHO": "CHA",
              "NOH": "NOP", "NOK": "NOP", "SEA": "OKC", "VAN": "MEM", "WSB": "WAS"}
transactions = {}
contract_events = {}  # bref_id -> [(date, team, "two-way" | "regular")], for the two-way check
with open("../processed/transactions.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["type"] in ("signed", "traded", "claimed", "expansion"):
            transactions.setdefault(row["bref_id"], []).append(row)
        if row["type"] == "signed" and row["to_team"]:
            kind = "two-way" if "two-way contract" in row["detail"] else "regular"
            contract_events.setdefault(row["bref_id"], []).append((row["date"], row["to_team"], kind))
        elif row["type"] == "converted":  # "converted X from a two-way contract to a regular contract"
            contract_events.setdefault(row["bref_id"], []).append((row["date"], row["from_team"], "regular"))

def arrivals_by_team(bref_id, year, team):
    """Ways the player joined `team` during the `year` season, June through June.
    Matched by date, not by which season's page the log filed it on -- late-June
    trades and early-July signings land on either side inconsistently."""
    start, end = f"{year - 1}-06-01", f"{year}-06-30"
    return {
        t["type"] for t in transactions.get(bref_id, [])
        if start <= t["date"] <= end and TEAM_CODES.get(t["to_team"], t["to_team"]) == team
    }

def signed_before_trade(bref_id, year, team, salary_teams):
    """The team that signed the player earlier in the `year` season, before he
    was traded/claimed to `team`, if that team has no salary row of its own
    that season (so its contract must be the one credited to `team`). Else None."""
    start, end = f"{year - 1}-06-01", f"{year}-06-30"
    moves = [t for t in transactions.get(bref_id, []) if start <= t["date"] <= end]
    arrived = min(t["date"] for t in moves if TEAM_CODES.get(t["to_team"], t["to_team"]) == team)
    origins = [
        t for t in moves
        if t["type"] == "signed" and t["date"] < arrived and t["to_team"]
        and TEAM_CODES.get(t["to_team"], t["to_team"]) not in salary_teams
    ]
    return TEAM_CODES.get(origins[-1]["to_team"], origins[-1]["to_team"]) if origins else None

def ended_on_two_way(bref_id, year, team):
    """True if the last contract `team` gave the player during the `year` season
    was a two-way. Uses the last one because players move between deals in a
    season: Marquese Chriss signed a regular deal with GSW in Sept 2019, went to
    a two-way in January and was converted back to regular in February (not a
    two-way); Daishen Nix signed an Exhibit 10 with MIN, then a two-way (two-way)."""
    start, end = f"{year - 1}-06-01", f"{year}-06-30"
    events = sorted(
        (d, kind) for d, t, kind in contract_events.get(bref_id, [])
        if start <= d <= end and TEAM_CODES.get(t, t) == team
    )
    return bool(events) and events[-1][1] == "two-way"

def re_signed(bref_id, year, team):
    """True if `team` signed the player to a new standard deal during the
    `year` season (not a two-way, not an extension of the deal he had)."""
    start, end = f"{year - 1}-06-01", f"{year}-06-30"
    return any(
        t["type"] == "signed" and start <= t["date"] <= end
        and TEAM_CODES.get(t["to_team"], t["to_team"]) == team
        and "two-way" not in t["detail"] and "extension" not in t["detail"]
        for t in transactions.get(bref_id, [])
    )

def signing_date(bref_id, year, team):
    """Earliest date `team` signed the player during the `year` season, or None."""
    start, end = f"{year - 1}-06-01", f"{year}-06-30"
    dates = [
        t["date"] for t in transactions.get(bref_id, [])
        if t["type"] == "signed" and start <= t["date"] <= end
        and TEAM_CODES.get(t["to_team"], t["to_team"]) == team
    ]
    return min(dates, default=None)

# a (team, salary) pair that closely matches one from an EARLIER season for
# the same player is almost certainly stretched dead money still being paid
# out, not a fresh salary for that team -- see the note below where this is
# used. Only counts if that earlier season also shows the player with
# ANOTHER team at the same time -- the actual signature of a trade-then-cut
# churn year, as opposed to a normal player just staying on one team for a
# few seasons on a flat-ish salary (which would otherwise false-positive
# constantly, since real contracts don't escalate much year to year either)
# -- AND the candidate salary itself is clearly above a normal minimum-level
# deal, since a legitimate back-to-back veteran-minimum re-signing with the
# same team (which rises ~5-10%/year on the scale) would otherwise get
# misflagged whenever an unrelated dead-money row from a different team
# happens to also exist that season.
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
# that same minimum rate but prorated for games remaining, so their total pay
# can land well below the full-season number while still being a genuine
# vet-min signing. So instead of a tight symmetric band around the full-season
# number, allow anything from a small floor (filters out things like single
# emergency call-ups) up to just above the full number.
RATIO_MAX = 1.03
RATIO_MIN = 0.22  # ~1/4 season minimum; below this it's an emergency/cup-of-coffee deal, not a real signing
flagged = []
skipped_no_bio = 0
skipped_same_stint = 0
skipped_carried_contract = 0
credited_to_signing_team = 0
skipped_two_way = 0
for bref_id, rows in by_player.items():
    b = bio.get(bref_id)
    if not b:
        skipped_no_bio += len(rows)
        continue
    debut_year = int(b["year_min"])
    # teams played for, per year (a player can have >1 row in a year if traded)
    teams_by_year = {}
    for row in rows:
        teams_by_year.setdefault(int(row["year"]), set()).add(row["team"])

    for row in rows:
        year = int(row["year"])
        yos = year - debut_year
        if yos < 1:
            continue  # skip rookie-min (yos 0) and glitches (yos<0)
        yos_capped = min(yos, 10)
        key = (year, yos_capped)
        if key not in min_scale:
            continue
        min_sal = min_scale[key]
        salary = float(row["salary"])
        if min_sal == 0:
            continue
        ratio = salary / min_sal
        if ratio > RATIO_MAX or ratio < RATIO_MIN:
            continue

        prev_teams = teams_by_year.get(year - 1)
        is_new_stint = prev_teams is None or row["team"] not in prev_teams
        # Same team as last season usually means a later year of the same
        # deal -- unless the log shows the team signed him again that season:
        # Indiana re-signed Lavoy Allen to a 1-year, $948,163 minimum in July
        # 2014 after paying him $3.1M the year before.
        if not is_new_stint and not re_signed(bref_id, year, row["team"]):
            skipped_same_stint += 1
            continue  # just another year of an existing contract, not a new min signing

        # A team change alone doesn't mean a new contract: a player traded,
        # claimed off waivers or taken in an expansion draft brings his old
        # deal with him (Pachulia to MIL in 2004, Middleton to MIL in 2013,
        # Rollins to WAS in 2023, Livingston to MEM in 2009 -- waived the same
        # day). So if the transactions log shows he got to this team that
        # season only that way, with no signing by the team, it's not a new
        # minimum signing. If the log has no arrival at all, keep the row:
        # the log isn't complete, and it sometimes records a waiver claim as
        # "signed" (Jeremy Lin to NYK, 2011), which also keeps the row.
        #
        # One catch: the salary data credits a contract traded mid-season to
        # the team holding it at the end, and often has no row at all for the
        # team that signed it. Nik Stauskas signed a 1-year minimum with
        # Portland in July 2018; the full $1,621,415 sits on Indiana's 2019
        # row (traded POR -> CLE -> HOU -> IND, then waived) and Portland has
        # none. Same for Carmelo Anthony (HOU -> CHI, 2019) and Rajon Rondo
        # (LAL -> CLE, 2022). So if a team with no salary row that season
        # signed him before he was traded here, this row is that team's
        # signing -- count it, credited to the team that signed him.
        team = row["team"]
        arrivals = arrivals_by_team(bref_id, year, team)
        if arrivals and "signed" not in arrivals:
            origin = signed_before_trade(bref_id, year, team, teams_by_year[year])
            if origin is None or (prev_teams is not None and origin in prev_teams):
                skipped_carried_contract += 1
                continue
            team = origin
            credited_to_signing_team += 1

        # Two-way contracts aren't minimum deals: they're a separate contract
        # type paying a flat amount (half the rookie minimum since 2023 --
        # Theo Maledon's $559,782 with Charlotte), which just happens to land
        # in the prorated-minimum range above.
        if ended_on_two_way(bref_id, year, team):
            skipped_two_way += 1
            continue

        # age on the day he signed, from the transactions log; Oct 1 of the
        # season if the log has no date (Bender signed July 26, 2019: 21.69,
        # not the 21.87 he'd be by Oct 1)
        birth = datetime.date.fromisoformat(b["birth_date"])
        signed_on = signing_date(bref_id, year, team)
        age_date = datetime.date.fromisoformat(signed_on) if signed_on else datetime.date(year - 1, 10, 1)
        age = (age_date - birth).days / 365.25

        # "salary cliff": what did they earn last season, before this min deal?
        # Exclude rows that are "dead money echoes" -- a near-identical
        # (team, salary) pair already appeared in an EARLIER season for this
        # player. That's the signature of a stretched waiver: e.g. DeAndre
        # Jordan was traded to Detroit in 2022 and immediately stretched, so
        # his ~$7.9M Detroit cap hit shows up again in 2023 even though he
        # was never actually on Detroit's roster that year and received no
        # new money -- it's the same old obligation still being paid out.
        # Using that as "what he earned last year" wildly overstates the
        # real cliff (or understates it, on the other side of the ledger).
        prev_rows = [
            r for r in rows
            if int(r["year"]) == year - 1
            and not is_dead_money_echo(bref_id, rows, r["team"], float(r["salary"]), year - 1)
        ]
        prev_salary = max((float(r["salary"]) for r in prev_rows), default=None)
        drop_pct = None
        if prev_salary and prev_salary > 0:
            drop_pct = round((prev_salary - salary) / prev_salary * 100, 1)

        flagged.append({
            "player": row["player"], "bref_id": bref_id, "year": year,
            "true_yos": yos, "salary": salary, "min_salary": min_sal, "ratio": round(ratio, 3),
            "team": team, "birth_date": b["birth_date"], "age_at_signing": round(age, 2),
            "prev_salary": prev_salary, "drop_pct": drop_pct,
        })

# A pay cut only counts once: the first time a player falls to the minimum.
# If he was already on a minimum deal -- earlier the same season (DeAndre
# Jordan: Lakers in September 2021, then Philadelphia in March 2022) or the
# season before (Anthony Bennett: Toronto 2015-16, then Brooklyn 2016-17) --
# a later minimum signing still counts as a signing, but has no drop. Measured
# the usual way, its "drop" comes from buyout or stretched money (Bennett's
# $3.65M Minnesota buyout) or from a salary he'd already lost, and the same
# fall would show up on the charts twice.
by_season = {}
for r in flagged:
    by_season.setdefault((r["bref_id"], r["year"]), []).append(r)
skipped_repeat_drop = 0
for (bref_id, year), rs in by_season.items():
    # same season: order by signing date; the first deal keeps its drop. A
    # signing with no date in the log goes last, bigger share of the minimum first
    rs.sort(key=lambda r: (signing_date(bref_id, year, r["team"]) or "9999", -r["ratio"]))
    already_min = (bref_id, year - 1) in by_season
    for i, r in enumerate(rs):
        if (i > 0 or already_min) and r["drop_pct"] is not None:
            r["drop_pct"] = None
            skipped_repeat_drop += 1

flagged.sort(key=lambda r: r["age_at_signing"])
with open("../processed/vetmin_signings.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "player", "bref_id", "year", "true_yos", "salary", "min_salary",
        "team", "birth_date", "age_at_signing", "prev_salary", "drop_pct", "ratio",
    ])
    w.writeheader()
    w.writerows(flagged)

print("salary rows skipped (no bio match):", skipped_no_bio)
print("skipped (same stint, not a new signing):", skipped_same_stint)
print("skipped (arrived by trade/claim/expansion, not signed):", skipped_carried_contract)
print("credited to the team that signed him (salary data had the trade partner):", credited_to_signing_team)
print("skipped (two-way contract, not a minimum deal):", skipped_two_way)
print("drop cleared (already on a minimum deal):", skipped_repeat_drop)
print("flagged vet-min rows (yos>=1, new stint):", len(flagged))
print()
print("Youngest 20 vet-min signings:")
for r in flagged[:20]:
    print(f"{r['age_at_signing']:.2f}  {r['player']:25s} {r['year']}  YOS={r['true_yos']:2d}  ${r['salary']:,.0f}  {r['team']}")

print()
print("Biggest 'salary cliff' vet-min signings (had real money the year before):")
cliffs = [r for r in flagged if r["drop_pct"] is not None]
cliffs.sort(key=lambda r: -r["drop_pct"])
for r in cliffs[:20]:
    print(f"{r['drop_pct']:5.1f}% drop  {r['player']:22s} {r['year']}  ${r['prev_salary']:,.0f} -> ${r['salary']:,.0f}  age {r['age_at_signing']:.1f}  {r['team']}")

print()
print("'Kuminga comps': age < 27 AND prior-season drop > 50%, youngest first")
comps = [r for r in flagged if r["drop_pct"] is not None and r["drop_pct"] > 50 and r["age_at_signing"] < 27]
comps.sort(key=lambda r: r["age_at_signing"])
for r in comps:
    print(f"{r['age_at_signing']:5.2f}  {r['player']:22s} {r['year']}  ${r['prev_salary']:,.0f} -> ${r['salary']:,.0f}  ({r['drop_pct']:.1f}% drop)  {r['team']}")

with open("../processed/kuminga_comps.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "player", "bref_id", "year", "true_yos", "salary", "min_salary",
        "team", "birth_date", "age_at_signing", "prev_salary", "drop_pct", "ratio",
    ])
    w.writeheader()
    w.writerows(comps)
