# Original project narrative (historical)

This preserves the earlier design and example results. The root README and current tests control implementation status. Planned integrations and old test counts below are not completion claims.

# Marketing Attribution Reality Check | Five models graded against known truth

The attribution debate (last-click vs everything else) is usually
unresolvable because true channel incrementality is unobservable. This lab
makes it observable: a 60k-user journey generator plants each channel's
TRUE incremental lift, then five attribution models are graded against
that ground truth. The result quantifies exactly how much money last-click
misallocates and why.

## Measured scoreboard (seeded, pinned by 5 tests)

```
model            MAE vs truth   paid_search share (truth = 14.3%)
removal_effect      0.038            19.1%
linear              0.046            23.4%
position_based      0.051            24.8%
first_click         0.092            13.2%
last_click          0.098            38.8%   <- 2.7x over-credited
```

The planted mechanism (which mirrors the real one): display and social
START journeys and genuinely raise conversion; paid search harvests the
final click on journeys other channels created. Last-click pays the
harvester — display gets 9.6% credit against 20.4% truth. A budget
reallocated on last-click numbers would cut the channels doing the work.

## What each model actually answers

Heuristics (last/first/linear/position) allocate CREDIT for observed
conversions — an accounting exercise. The removal-effect model (logistic
conversion model over channel presence; contribution = predicted
conversions lost when a channel is zeroed) estimates INCREMENTALITY — the
budget question. They are different questions; the scoreboard shows the
cost of confusing them. And the honest ceiling: even removal-effect is
observational — the gold standard is geo holdouts / lift tests, i.e. the
experiments in the sibling ab-testing-framework and causal-inference
projects. This lab is the bridge between "credit rules" and "causal spend
decisions."

## Run
```bash
pip install pandas numpy scikit-learn pytest
PYTHONPATH=src python src/attribution/generate.py
PYTHONPATH=src pytest tests/ -q     # 5 tests
```
