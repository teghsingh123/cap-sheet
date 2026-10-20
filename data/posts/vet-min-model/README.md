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

**Baseline to beat: 58.1%.** Guessing "he stays" every time is right that
often. A model that can't beat it isn't useful.

Signings from 2023-24, the last season in the salary data, have no next
season to check, so they're already left out of `prove_it.json`.

## Inputs (known at signing)

| Column | From | Notes |
|---|---|---|
| `age` | `prove_it.json` `age` | Age on the signing date |
| `years_service` | `all_signings.json` `yearsOfService` | Not in `prove_it.json`: join on `brefId` + `year` + salary (`vetMinSalary` = `salary`) |
| `draft_pick` | `prove_it.json` `draftPick` | Undrafted (`null`) -> 61 |
| `undrafted` | `draftPick` is `null` | 1 or 0 |
| `season` | `prove_it.json` `year` | Year the season ends: 2016 = 2015-16 |

Label: `out_next` = 1 if `outcome == "flamed_out"`, else 0.

Both JSON files are in `../../../web/public/data/kuminga-line/` and are
built by `../kuminga-line/05_build_extra_charts.py` (the `prove_it` block
has the "out next season" logic).

## Plan

1. **Build the dataset:** one row per signing, the columns above, saved as
   a CSV. Check: 632 rows, `out_next` sums to 265, no empty
   `years_service`, latest `season` is 2023.
2. **Baseline:** 58.1% from always guessing "stays".
3. **Split by time:** train on older seasons, test on recent ones, so the
   model never learns from the future.
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

Scripts go in this folder and run from inside it, after the shared pipeline
(`../../pipeline/`) and the Kuminga post's scripts (`../kuminga-line/`).
JSON the post loads goes in `../../../web/public/data/vet-min-model/`. Needs
`py -m pip install pandas scikit-learn`.

If the post ends up with a different slug, rename this folder to match its
folder in `web/src/posts/`.
