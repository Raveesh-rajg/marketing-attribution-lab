import pathlib
import sys

import pandas as pd
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from attribution.generate import generate, OUT
from attribution import models


@pytest.fixture(scope="session")
def data():
    generate(n_users=40_000)
    df = pd.read_csv(OUT / "touchpoints.csv")
    truth = pd.read_csv(OUT / "true_lifts.csv")
    return df, truth


class TestShares:
    def test_every_model_sums_to_one(self, data):
        df, truth = data
        for fn in (models.last_click, models.first_click, models.linear,
                   models.position_based, models.removal_effect):
            assert fn(df).sum() == pytest.approx(1.0, abs=0.01), fn.__name__


class TestPlantedDistortion:
    def test_last_click_overcredits_paid_search(self, data):
        df, truth = data
        lc = models.last_click(df)
        t = models.true_shares(truth)
        assert lc["paid_search"] > t["paid_search"] * 1.8

    def test_last_click_starves_upper_funnel(self, data):
        df, truth = data
        lc = models.last_click(df)
        t = models.true_shares(truth)
        assert lc["display"] < t["display"] * 0.6


class TestRemovalEffect:
    def test_removal_beats_all_heuristics(self, data):
        df, truth = data
        sb = models.scoreboard(df, truth)
        assert sb.iloc[0].model == "removal_effect"

    def test_removal_close_to_truth(self, data):
        df, truth = data
        sb = models.scoreboard(df, truth).set_index("model")
        assert sb.loc["removal_effect"].mae_vs_truth < 0.05
        assert sb.loc["removal_effect"].mae_vs_truth < \
               sb.loc["last_click"].mae_vs_truth / 2
