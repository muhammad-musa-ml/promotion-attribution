# promotion-attribution

I wrote a small rule that credits job applications to promoted jobs, and measured it against two simpler ways of counting on synthetic logs where I know why each application happened.

## What it does

An employer promotes a job. Users see it (an impression), some click it, some apply. `attribute()` credits an application to a promotion when the same user clicked that promotion at most 7 days before applying, or else saw it at most 24 hours before. The touch has to fall inside the promotion and cannot come after the application. A click beats an impression, the latest of its kind wins, and a user who applies twice to one job counts once.

The log is allowed to be messy. Events are deduplicated by id and sorted by time before anything is credited, so repeated events and late arrivals do not change the result. Tests check this, including 25 shuffles of a 135-event log.

## Why

A number shown to an employer is only useful if the rule behind it is stated and holds up on a real log: retries, late events, double applications. I wanted a version small enough to read in one sitting, with a test for each of those cases and a measurement of how much the choices change the total.

## Run

Python 3.10 or later, standard library only (pytest for the tests).

```
python -m pytest
python -m promoattr report        # seeds 1 to 10, writes results/
python -m promoattr run --seed 7  # one seed, printed
```

## Results

Written by `python -m promoattr report` (`results/summary.md`, per-seed rows in `results/by_seed.csv`). Each cell is the mean over 10 seeds, with the lowest and highest seed in brackets. A seed is 2,000 users and 30 jobs, 10 of them promoted; it has 2,611 to 2,755 events and 161 to 199 applications that the generator made because of a promotion.

| method | credited / caused | precision | recall |
| --- | --- | --- | --- |
| period share | 3.35 (3.06 to 3.98) | 29.2% (24.4% to 32.0%) | 97.2% (95.5% to 99.5%) |
| windows in arrival order (click 7d, view 24h) | 1.43 (1.31 to 1.62) | 65.6% (58.2% to 70.3%) | 93.7% (91.5% to 98.3%) |
| attribute (click 7d, view 24h) | 1.44 (1.32 to 1.57) | 69.8% (63.6% to 75.9%) | 100.0% (100.0% to 100.0%) |

Length of the view window, click window fixed at 7 days:

| method | credited / caused | precision | recall |
| --- | --- | --- | --- |
| attribute (click 7d, view off) | 0.66 (0.61 to 0.70) | 100.0% (100.0% to 100.0%) | 65.7% (60.9% to 69.7%) |
| attribute (click 7d, view 1h) | 0.67 (0.62 to 0.72) | 97.7% (95.2% to 99.2%) | 65.7% (60.9% to 69.7%) |
| attribute (click 7d, view 6h) | 0.85 (0.80 to 0.91) | 87.0% (83.1% to 89.7%) | 74.3% (67.4% to 78.7%) |
| attribute (click 7d, view 24h) | 1.44 (1.32 to 1.57) | 69.8% (63.6% to 75.9%) | 100.0% (100.0% to 100.0%) |
| attribute (click 7d, view 72h) | 2.32 (2.17 to 2.61) | 43.2% (38.3% to 46.1%) | 100.0% (100.0% to 100.0%) |

`credited / caused` is credit entries divided by the applications the generator made because of a promotion. Above 1.00 the report claims more than the promotions caused.

- Crediting every applicant who applied to a promoted job during the promotion (`period share`) claimed about 3.4 times the caused applications, and 29% of its credits were right.
- Applying the same windows in one pass over the log in arrival order (`arrival_order`) found 93.7% of the caused applicants, against 100% for the sorted version, and had lower precision (65.6% against 69.8%). It credits a repeated application once per copy.
- The view window moves the total more than anything else. With view credit off, every credit is right and a third of the caused applicants are missed; at 24 hours all of them are found and 30% of the credits are wrong; at 72 hours the total is 2.3 times the caused count.

## What this does not show

- All data is synthetic. I set the cause of every application in `promoattr/generate.py`, and the shares of each kind of user are the constants at the top of that file. The table describes that mix. It says nothing about real traffic or real conversion rates, and moving the shares moves the numbers.
- The rule's 100% recall is by construction: every caused applicant I generated applies inside the windows.
- Whether a promotion caused an application cannot be read from a log. A holdout experiment is the way to measure that; this repository only counts touches before applications.
- One touch is credited per application. There is no multi-touch split, no identity matching across devices, no bot filtering and no weighting by surface.

## Files

- `promoattr/events.py`: event and promotion types, JSONL reader.
- `promoattr/attribute.py`: deduplication and the rule.
- `promoattr/baselines.py`: `period_share` and `arrival_order`.
- `promoattr/generate.py`: seeded generator with the cause of each application.
- `promoattr/evaluate.py`: scoring, the view-window sweep, the results files.
- `tests/`: 32 tests.
