"""Attribution models, all graded against the planted truth.

Heuristics (last/first/linear/position) allocate CREDIT for observed
conversions; the removal-effect model estimates INCREMENTAL contribution —
different questions, and the comparison to truth shows how much that
distinction costs. Truth here = each channel's share of total incremental
lift, so models are compared on SHARE allocation (sums to 1).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _shares(s: pd.Series) -> pd.Series:
    return (s / s.sum()).round(4)


def last_click(df: pd.DataFrame) -> pd.Series:
    conv = df[(df.converted == 1) & df.is_last]
    return _shares(conv.groupby("channel").size())


def first_click(df: pd.DataFrame) -> pd.Series:
    conv = df[(df.converted == 1) & (df.position == 0)]
    return _shares(conv.groupby("channel").size())


def linear(df: pd.DataFrame) -> pd.Series:
    conv = df[df.converted == 1].copy()
    conv["w"] = 1 / conv.groupby("user_id").channel.transform("size")
    return _shares(conv.groupby("channel").w.sum())


def position_based(df: pd.DataFrame) -> pd.Series:
    """40/20/40: first and last touch get 40% each, middles split 20%."""
    conv = df[df.converted == 1].copy()
    n = conv.groupby("user_id").channel.transform("size")
    is_first = conv.position == 0
    w = np.where(n == 1, 1.0,
        np.where(n == 2, 0.5,
        np.where(is_first | conv.is_last, 0.4, 0.2 / (n - 2).clip(lower=1))))
    conv["w"] = w
    return _shares(conv.groupby("channel").w.sum())


def removal_effect(df: pd.DataFrame) -> pd.Series:
    """Logistic-model removal effect: fit P(convert | channel-presence
    indicators) at the user grain, then measure each channel's contribution
    as the drop in predicted conversions when it is 'removed' (indicator
    zeroed). This estimates INCREMENTALITY from presence patterns — the
    data-driven family last-click pretends to be."""
    from sklearn.linear_model import LogisticRegression

    user = (df.assign(one=1)
              .pivot_table(index="user_id", columns="channel",
                           values="one", aggfunc="max", fill_value=0))
    y = df.groupby("user_id").converted.max().reindex(user.index)
    model = LogisticRegression(max_iter=1000).fit(user.values, y)
    base = model.predict_proba(user.values)[:, 1].sum()
    drops = {}
    for j, ch in enumerate(user.columns):
        X = user.values.copy()
        X[:, j] = 0
        drops[ch] = base - model.predict_proba(X)[:, 1].sum()
    return _shares(pd.Series(drops))


def true_shares(true_lifts: pd.DataFrame) -> pd.Series:
    s = true_lifts.set_index("channel").true_lift
    return _shares(s)


def scoreboard(df: pd.DataFrame, true_lifts: pd.DataFrame) -> pd.DataFrame:
    truth = true_shares(true_lifts)
    models = {"last_click": last_click(df), "first_click": first_click(df),
              "linear": linear(df), "position_based": position_based(df),
              "removal_effect": removal_effect(df)}
    rows = []
    for name, shares in models.items():
        shares = shares.reindex(truth.index).fillna(0)
        mae = float((shares - truth).abs().mean())
        worst = (shares - truth).abs().idxmax()
        rows.append({"model": name, "mae_vs_truth": round(mae, 4),
                     "worst_channel": worst,
                     "paid_search_share": float(shares["paid_search"]),
                     "paid_search_truth": float(truth["paid_search"])})
    return pd.DataFrame(rows).sort_values("mae_vs_truth").reset_index(drop=True)
