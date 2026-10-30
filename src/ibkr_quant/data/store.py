"""本地 Parquet 存储：data/raw/<bar_size>/<SYMBOL>.parquet，重复拉取时自动合并去重。"""
from __future__ import annotations

import pandas as pd

from ..config import RAW_DIR


def _path(symbol: str, bar_size: str):
    d = RAW_DIR / bar_size.replace(" ", "_")
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{symbol.upper()}.parquet"


def save_bars(df: pd.DataFrame, symbol: str, bar_size: str = "1 day") -> None:
    p = _path(symbol, bar_size)
    if p.exists():
        old = pd.read_parquet(p)
        df = pd.concat([old, df])
        df = df[~df.index.duplicated(keep="last")].sort_index()
    df.to_parquet(p)


def load_bars(symbol: str, bar_size: str = "1 day") -> pd.DataFrame:
    p = _path(symbol, bar_size)
    if not p.exists():
        raise FileNotFoundError(f"没有 {symbol} 的 {bar_size} 数据，先运行 scripts/fetch_history.py")
    return pd.read_parquet(p)


def load_closes(symbols: list[str], bar_size: str = "1 day") -> pd.DataFrame:
    """多只股票的收盘价对齐成一张宽表。"""
    return pd.DataFrame({s.upper(): load_bars(s, bar_size)["close"] for s in symbols})
