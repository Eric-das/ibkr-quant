"""最基础的收益/风险统计，后面做因子和回测时在这里往上加。"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def simple_returns(prices: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    return prices.pct_change().dropna(how="all")


def log_returns(prices: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    return np.log(prices / prices.shift(1)).dropna(how="all")


def summary(prices: pd.DataFrame) -> pd.DataFrame:
    """年化收益、年化波动、Sharpe（rf=0）、最大回撤。"""
    r = simple_returns(prices)
    ann_ret = (1 + r).prod() ** (TRADING_DAYS / len(r)) - 1
    ann_vol = r.std() * np.sqrt(TRADING_DAYS)
    nav = (1 + r).cumprod()
    mdd = (nav / nav.cummax() - 1).min()
    return pd.DataFrame(
        {"ann_return": ann_ret, "ann_vol": ann_vol, "sharpe": ann_ret / ann_vol, "max_drawdown": mdd}
    )
