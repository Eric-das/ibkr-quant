"""从 IBKR 拉历史 K 线。"""
from __future__ import annotations

import pandas as pd
from ib_async import IB, Contract, Stock, util

from ..config import SETTINGS


def stock(symbol: str, exchange: str = "SMART", currency: str = "USD") -> Stock:
    return Stock(symbol, exchange, currency)


def historical_bars(
    ib: IB,
    contract: Contract,
    duration: str | None = None,
    bar_size: str | None = None,
    what_to_show: str | None = None,
    use_rth: bool | None = None,
    end: str = "",
) -> pd.DataFrame:
    """返回 DatetimeIndex 的 OHLCV DataFrame，列：open high low close volume average barCount。

    duration 例："1 Y" "6 M" "30 D"；bar_size 例："1 day" "1 hour" "5 mins"。
    IBKR 对单次请求的长度有限制（分钟线一般一次最多拉几天），需要更长的话分段请求。
    """
    h = SETTINGS.get("history", {})
    bars = ib.reqHistoricalData(
        contract,
        endDateTime=end,
        durationStr=duration or h.get("duration", "1 Y"),
        barSizeSetting=bar_size or h.get("bar_size", "1 day"),
        whatToShow=what_to_show or h.get("what_to_show", "TRADES"),
        useRTH=use_rth if use_rth is not None else h.get("use_rth", True),
        formatDate=1,
    )
    df = util.df(bars)
    if df is None or df.empty:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    df.attrs["symbol"] = getattr(contract, "symbol", "")
    return df
