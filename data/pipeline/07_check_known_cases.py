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

with open("../../web/public/data/all_signings.json", encoding="utf-8") as f:
    signings = json.load(f)["signings"]
with open("../../web/public/data/prove_it.json", encoding="utf-8") as f:
    prove_it = json.load(f)["signings"]

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
    ("No signing from the last season of data has a 'next season' outcome",
     all(p["year"] < max(s["year"] for s in signings) for p in prove_it)),
]

failed = 0
for name, ok in checks:
    print(("PASS  " if ok else "FAIL  ") + name)
    failed += not ok
sys.exit(1 if failed else 0)
