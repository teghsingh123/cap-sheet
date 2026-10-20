"""
Checks the final JSON outputs against cases I've verified by hand against
outside sources (Basketball-Reference, Spotrac, news reports). If a source
or rule change breaks one of them, this fails loudly instead of the article
quietly going wrong.

Bender is here because the original salary file was missing his 2019-20
Milwaukee deal, which made Tskitishvili look like the youngest answer. The
rest are the edge cases the article walks through.
"""
import json, sys

with open("../../../web/public/data/kuminga-line/all_signings.json", encoding="utf-8") as f:
    signings = json.load(f)["signings"]
with open("../../../web/public/data/kuminga-line/prove_it.json", encoding="utf-8") as f:
    prove_it = json.load(f)["signings"]
with open("../../../web/public/data/kuminga-line/young_fa.json", encoding="utf-8") as f:
    young_fa = json.load(f)["signings"]

def new_contract(bref_id, year, team):
    return any(s["brefId"] == bref_id and s["year"] == year and s["team"] == team for s in young_fa)

def signing(bref_id, year, team):
    return next((s for s in signings if s["brefId"] == bref_id and s["year"] == year and s["team"] == team), None)

def outcomes(bref_id, year):
    return {p["outcome"] for p in prove_it if p["brefId"] == bref_id and p["year"] == year}

top10 = sorted(
    (s for s in signings if s["isKumingaComp"] and s["draftPick"] and s["draftPick"] <= 10),
    key=lambda s: s["age"],
)

checks = [
    ("Bender's 2019-20 Milwaukee minimum deal is in the data",
     signing("bendedr01", 2020, "MIL") is not None),
    ("Bender is the youngest top-10-pick comp",
     bool(top10) and top10[0]["brefId"] == "bendedr01"),
    ("Tskitishvili's 2005-06 Minnesota deal is still a comp",
     (s := signing("tskitni01", 2006, "MIN")) is not None and s["isKumingaComp"]),
    ("DeAndre Jordan never shows as a fake bounce-back",
     "bounced_back" not in outcomes("jordade01", 2022) | outcomes("jordade01", 2023)),
    ("Jordan's 2022-23 Denver re-signing still counts as a minimum deal",
     signing("jordade01", 2023, "DEN") is not None),
    ("Danny Green's 2022-23 minimum deal ends in 'flamed out'",
     outcomes("greenda02", 2023) == {"flamed_out"}),
    ("Joe Johnson's 2016 Miami deal bounces back to Utah's $11M",
     outcomes("johnsjo02", 2016) == {"bounced_back"}),
    ("Pachulia's 2004-05 Milwaukee year is his carried-over rookie deal, not a new signing",
     signing("pachuza01", 2005, "MIL") is None),
    ("Rollins' 2023-24 Washington year came in the Chris Paul trade, not a new signing",
     signing("rolliry01", 2024, "WAS") is None),
    ("Livingston's 2009 Memphis stint was a trade-and-waive, not a signing",
     signing("livinsh01", 2009, "MEM") is None),
    ("Stauskas' 2019 Indiana stop was a trade; his Cleveland deal that month was a real signing",
     signing("stausni01", 2019, "IND") is None and signing("stausni01", 2019, "CLE") is not None),
    ("Jordan's 2021-22 fall is counted once: the Lakers deal has the drop, Philadelphia's doesn't",
     (s := signing("jordade01", 2022, "LAL")) is not None and s["dropPct"]
     and (p := signing("jordade01", 2022, "PHI")) is not None and p["dropPct"] is None),
    ("Jordan's 2022-23 Denver deal has no drop measured from Detroit buyout money",
     signing("jordade01", 2023, "DEN")["dropPct"] is None),
    ("Bennett is a comp at 22.6 (Toronto) but not again at 23.6 (Brooklyn, after a min deal)",
     signing("bennean01", 2016, "TOR")["isKumingaComp"] and not signing("bennean01", 2017, "BKN")["isKumingaComp"]),
    ("Fredette's fall is his 2014 Bulls deal, not the 2014-15 Pelicans deal after it",
     not signing("fredeji01", 2015, "NOP")["isKumingaComp"]),
    ("Stauskas' fall is his July 2018 Portland minimum, not the Cleveland pickup in February",
     (s := signing("stausni01", 2019, "POR")) is not None and s["isKumingaComp"] and s["ratioOfMin"] == 1.0
     and signing("stausni01", 2019, "CLE")["dropPct"] is None),
    ("Signings credited to the trade partner are counted for the team that signed them",
     all(signing(*k) is not None for k in [("anthoca01", 2019, "HOU"), ("wadedw01", 2018, "CLE"), ("rondora01", 2022, "LAL")])),
    ("Two-way contracts aren't minimum signings (Maledon 2022-23 CHA, Nix 2023-24 MIN)",
     signing("maledth01", 2023, "CHA") is None and signing("nixda01", 2024, "MIN") is None),
    ("Chriss stays: his GSW two-way was converted back to a regular deal",
     (s := signing("chrisma01", 2020, "GSW")) is not None and s["isKumingaComp"]),
    ("Same-team re-signings count: Indiana re-signed Lavoy Allen to a minimum in July 2014",
     (s := signing("allenla01", 2015, "IND")) is not None and s["dropPct"] > 50),
    ("Korkmaz's July 2019 re-signing with Philadelphia (option declined) counts",
     signing("korkmfu01", 2020, "PHI") is not None),
    ("Ages are on the signing date: Bender signed July 26, 2019 at 21.69",
     abs(signing("bendedr01", 2020, "MIL")["age"] - 21.69) < 0.01),
    ("A prorated deal followed by a normal minimum isn't a bounce-back (Damon Jones 1999-00)",
     outcomes("jonesda01", 2000) == {"stuck"}),
    ("Young FA chart: a sign-and-trade is a new contract for the new team (Lonzo Ball to CHI, 2021)",
     new_contract("balllo01", 2022, "CHI")),
    ("Young FA chart: a plain trade isn't a new contract (Jordan Poole to WAS, 2023)",
     not new_contract("poolejo01", 2024, "WAS")),
    ("Young FA chart: a restricted free agent re-signing counts (Deandre Ayton, PHX 2022)",
     new_contract("aytonde01", 2023, "PHX")),
    ("Pressey's 2015-16 Philadelphia hardship deal still counts as a signing",
     any(s["brefId"] == "pressph01" and s["year"] == 2016 and s["team"] == "PHI" for s in signings)),
    ("No signing from the last season of data has a 'next season' outcome",
     all(p["year"] < max(s["year"] for s in signings) for p in prove_it)),
]

failed = 0
for name, ok in checks:
    print(("PASS  " if ok else "FAIL  ") + name)
    failed += not ok
sys.exit(1 if failed else 0)
