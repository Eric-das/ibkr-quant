import numpy as np
import pandas as pd

from ibkr_quant.analysis.returns import log_returns, simple_returns, summary


def _prices():
    idx = pd.bdate_range("2024-01-01", periods=300)
    return pd.DataFrame({"A": np.linspace(100, 130, 300), "B": 100 * 1.001 ** np.arange(300)}, index=idx)


def test_returns_shapes():
    p = _prices()
    assert len(simple_returns(p)) == len(p) - 1
    assert np.allclose(log_returns(p)["B"], np.log(1.001))


def test_summary_columns():
    s = summary(_prices())
    assert list(s.columns) == ["ann_return", "ann_vol", "sharpe", "max_drawdown"]
    assert (s["max_drawdown"] <= 0).all()
