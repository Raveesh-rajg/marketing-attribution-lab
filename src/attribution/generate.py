"""Customer-journey generator with KNOWN true channel contributions.

The eternal attribution fight — last-click vs everything else — is usually
unresolvable because truth is unobservable. Here it isn't: each channel
has a planted true incremental effect on conversion, so every attribution
model can be graded against ground truth.

Planted structure (the classic distortion):
  * display + social are UPPER-funnel: they start journeys and raise
    conversion, but rarely get the final touch;
  * paid_search is LOWER-funnel: modest true lift, but it harvests the
    last click on journeys other channels created -> last-click will
    massively over-credit it;
  * email mid-funnel; organic converts navigators (high truth, no spend).
"""

from __future__ import annotations

import csv
import pathlib
import random

rng = random.Random(20260717)
OUT = pathlib.Path(__file__).resolve().parents[2] / "data"

# channel -> (true incremental lift on conversion logit, P(appears early), P(last touch | present))
CHANNELS = {
    "display":     {"lift": 0.50, "starter": 0.35, "closer": 0.05},
    "social":      {"lift": 0.60, "starter": 0.30, "closer": 0.10},
    "email":       {"lift": 0.45, "starter": 0.10, "closer": 0.20},
    "paid_search": {"lift": 0.35, "starter": 0.15, "closer": 0.45},
    "organic":     {"lift": 0.55, "starter": 0.10, "closer": 0.20},
}
BASE_LOGIT = -2.8


def generate(n_users: int = 60_000) -> dict:
    OUT.mkdir(exist_ok=True)
    import math
    rows = []
    conversions = 0
    for u in range(n_users):
        # journey: 1-5 touches; starters weighted first, closers weighted last
        n_touch = rng.choices([1, 2, 3, 4, 5], weights=[25, 30, 25, 13, 7])[0]
        starters = [c for c in CHANNELS for _ in range(int(CHANNELS[c]["starter"] * 100))]
        closers = [c for c in CHANNELS for _ in range(int(CHANNELS[c]["closer"] * 100))]
        mids = list(CHANNELS)
        path = [rng.choice(starters)]
        while len(path) < n_touch - 1:
            path.append(rng.choice(mids))
        if n_touch > 1:
            path.append(rng.choice(closers))
        present = set(path)
        logit = BASE_LOGIT + sum(CHANNELS[c]["lift"] for c in present)
        converted = rng.random() < 1 / (1 + math.exp(-logit))
        conversions += converted
        for pos, ch in enumerate(path):
            rows.append({"user_id": f"u{u}", "position": pos, "channel": ch,
                         "is_last": pos == len(path) - 1,
                         "converted": int(converted)})
    with open(OUT / "touchpoints.csv", "w", newline="") as f:
        w = csv.DictWriter(f, rows[0].keys()); w.writeheader(); w.writerows(rows)
    truth = {c: CHANNELS[c]["lift"] for c in CHANNELS}
    with open(OUT / "true_lifts.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["channel", "true_lift"])
        for c, l in truth.items():
            w.writerow([c, l])
    return {"users": n_users, "touches": len(rows), "conversions": conversions}


if __name__ == "__main__":
    print(generate())
