# vet-min-model

Second Cap Sheet post.

## The question

**When an NBA player takes a pay cut down to the veteran's minimum, can we
predict whether he'll be out of the league the next season?**

- **Pay cut down to the minimum:** a veteran-minimum signing where he made
  more the season before (`dropPct > 0`). Not raises, not first-ever
  minimum deals. These are players whose market value just dropped.
- **Out of the league the next season:** no NBA salary the following season,
  or one under 22% of the minimum (Danny Green's two games with Philadelphia
  in 2023-24 count as out). This is the `flamed_out` outcome in the Kuminga
  post's `prove_it.json`.
- **Predict:** using only what was known the day he signed. Nothing from
  after the signing can be an input.

It follows from "The Kuminga Line," which ended on "taking the minimum isn't
automatically the end." This tests it: who gets back, and who washes out?

## The data (as of the current pipeline)

| | |
|---|---|
| Real pay-cut signings with a known next season | 632 |
| Out of the league the next season | 265 (41.9%) |
| Stayed | 367 (58.1%) |

Guessing "he stays" every time is right 58.1% of the time across all 632. A
model that can't beat that guess isn't useful. **The number to beat is 56.4%,**
the same guess on the 181 test signings, since models are scored on those.

Signings from 2023-24, the last season in the salary data, have no next
season to check, so they're already left out of `prove_it.json`.

## Inputs (known at signing)

| Column | From | Notes |
|---|---|---|
| `age` | `prove_it.json` `age` | Age on the signing date |
| `years_service` | `all_signings.json` `yearsOfService` | Not in `prove_it.json`: join on `brefId` + `year` + salary (`vetMinSalary` = `salary`) |
| `draft_pick` | `prove_it.json` `draftPick`, then `old_draft_picks.csv` | Undrafted -> 61. Picks over 61 are capped at 61 |
| `undrafted` | No pick in either source | 1 or 0. Don't use a blank `draftPick` alone: it's also blank for anyone drafted before 1990 |
| `season` | `prove_it.json` `year` | Year the season ends: 2016 = 2015-16 |
| `prev_salary_m` | `all_signings.json` `prevSalary` | The season before, in millions of dollars. Same join as `years_service` |
| `drop_pct` | `all_signings.json` `dropPct` | Size of the pay cut, 0 to 100. Same join as `years_service` |
| `prev_mpg` | `season_stats.csv` | Minutes per game the season before signing. Blank -> 0 |
| `prev_games_pct` | `season_stats.csv` | Share of the season's games he played. Blank -> 0 |
| `prev_bpm` | `season_stats.csv` | Box Plus/Minus. Blank -> -2, about replacement level, because 0 means league average |
| `missed_prev_season` | `prev_mpg` is blank | 1 or 0. True for 24 signings |
| `mpg_change` | `season_stats.csv` | `prev_mpg` minus minutes per game two seasons before signing. Blank -> 0 |
| `bpm_change` | `season_stats.csv` | `prev_bpm` minus BPM two seasons before signing. Blank -> 0 |

Label: `out_next` = 1 if `outcome == "flamed_out"`, else 0.

Both JSON files are in `../../../web/public/data/kuminga-line/` and are
built by `../kuminga-line/05_build_extra_charts.py` (the `prove_it` block
has the "out next season" logic).

## Plan

1. **Build the dataset:** one row per signing, the columns above, saved as
   a CSV. Check: 632 rows, `out_next` sums to 265, no empty
   `years_service`, latest `season` is 2023.
2. **Baseline:** always guess "stays": 58.1% overall, 56.4% on the test set.
3. **Split by time:** train on seasons before 2018 (451 signings), test on
   2018 and later (181), so the model never learns from the future.
4. **Train:** logistic regression (scikit-learn).
5. **Evaluate:** accuracy against the baseline, which inputs mattered, and
   the players it got wrong.
6. **Write it up** as the post.

## Open choices

- **Scope:** pay cuts only (632, the default above), or every minimum
  signing (1,538)? The others would need an "out next season" label
  computed the same way `prove_it` does it.
- **Outcome:** "out of the league," or "got a real contract again"
  (`bounced_back`, 80 cases: rarer and harder to predict, but closer to the
  Kuminga story)?

## Running

Scripts go in this folder, after the shared pipeline (`../../pipeline/`) and
the Kuminga post's scripts (`../kuminga-line/`). JSON the post loads goes in
`../../../web/public/data/vet-min-model/`. Needs
`python -m pip install pandas scikit-learn`.

Run them in this order:

1. `scrape_old_drafts.py`: writes `old_draft_picks.csv`. Only needed if that
   file is missing. Its downloaded pages stay out of git.
2. `scrape_season_stats.py`: writes `season_stats.csv`. Only needed if that
   file is missing. Its downloaded pages stay out of git.
3. `08_build_dataset.py`: writes `dataset.csv`.
4. `09_train_model.py`: prints the test results.
5. `10_validate.py`: prints the validation results.

If the post ends up with a different slug, rename this folder to match its
folder in `web/src/posts/`.

## Results

Test set: 181 signings, 2018-2023. Baseline: 56.4% (always guess "stays").

| Version | Features | Train | Test | Predicted out | Notes |
|---|---|---|---|---|---|
| V1 | age, years_service, draft_pick, undrafted, season | 60.8% | 54.1% | 12 (4 correct) | Below baseline. Mostly guesses "stays". |
| V2 | V1 + prev_salary_m, drop_pct | 61.2% | 56.9% | 5 (3 correct) | Beats baseline by one signing (103 vs 102 correct), which could be luck. Fewer wrong "out" calls, but catches fewer real outs. |
| V3 | V2 + prev_mpg, prev_games_pct, prev_bpm, missed_prev_season | 62.1% | 55.2% | 14 (6 correct) | Below baseline by two signings. Catches the most real outs, but ranks players worse than V2. |

79 of the 181 test signings were really out. V1 caught 4, V2 caught 3 and V3
caught 6, so accuracy alone doesn't tell the whole story.

Ranking score (AUC): if you pick one player who was out and one who stayed, how
often does the model give the out player the higher chance? 50% is a coin flip.
V2 scored 63% and V3 scored 55%, so adding stats spread the probabilities out
but sorted players worse.

The test group looks healthier than the training group but washed out more
often: 18.1 minutes vs 16.0, BPM of -1.7 vs -2.7, and age 29.5 vs 30.0, with
43.6% out vs 41.2%. So what the model learned from older seasons may not hold
for recent ones. Stats may also miss why players leave, such as injury or
retirement. This is a theory, not a tested result.

`prev_salary_m` isn't adjusted for the salary cap, and salaries rose over time (the median was
$1.65M through 2005 and $5.25M from 2018 on), so it may not carry over well
from the training seasons to the test seasons.

## Validation

To try ideas without tuning against the test set, `10_validate.py` trains on
seasons before 2012 (272 signings) and checks on 2012-2017 (179). Baseline:
61.5% (110 correct). V4 was only run here, so the test set stays untouched
until a final run.

Target: at least 66% accuracy and a 62% ranking score, on validation and then
on the test set.

| Version | Features | Logistic accuracy | Logistic ranking | Forest train | Forest accuracy | Forest ranking |
|---|---|---|---|---|---|---|
| V1 | as above | 60.9% | 49.1% | 69.1% | 58.7% | 50.5% |
| V2 | as above | 62.0% | 48.7% | 76.5% | 59.2% | 57.7% |
| V3 | as above | 59.8% | 55.3% | 78.3% | 61.5% | **60.3%** |
| V4 | V3 + mpg_change, bpm_change | 55.9% | 51.7% | 78.7% | 60.3% | 59.5% |

The forest is a random forest with 500 trees and `min_samples_leaf=10`.

- **No version beats the baseline by more than one signing.** Accuracy can swing
  by about 6 signings by chance alone, so the order could be luck.
- **Forest V3 is the best so far.** Its ranking score rises as features are added,
  so a model that can combine features gets more out of them.
- **V4 didn't help.** The trend features scored slightly worse, so V3 stays.
- **V2's 63% ranking on the test set didn't hold up:** logistic V2 scored 48.7%
  here. Logistic V3 scored about 55% on both, which doesn't support the theory
  that the league changed after 2018.
