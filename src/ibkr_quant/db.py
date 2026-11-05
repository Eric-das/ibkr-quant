"""PostgreSQL 连接与 K 线表的读写。表 bars(symbol, bar_size, ts, open, high, low, close, volume, average, bar_count)。

    from ibkr_quant.db import engine, upsert_bars, read_bars
"""
from __future__ import annotations

import os

import pandas as pd
import sqlalchemy as sa

from .config import PROJECT_ROOT  # noqa: F401  (确保 .env 已加载)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg:///ibkr_quant")
engine = sa.create_engine(DATABASE_URL, pool_pre_ping=True)

_DDL = """
create table if not exists bars (
    symbol    text        not null,
    bar_size  text        not null,
    ts        timestamptz not null,
    open      double precision,
    high      double precision,
    low       double precision,
    close     double precision,
    volume    double precision,
    average   double precision,
    bar_count integer,
    primary key (symbol, bar_size, ts)
);
create index if not exists bars_symbol_ts on bars (symbol, ts);
"""


def init_db() -> None:
    with engine.begin() as c:
        for stmt in filter(None, (s.strip() for s in _DDL.split(";"))):
            c.execute(sa.text(stmt))


def upsert_bars(df: pd.DataFrame, symbol: str, bar_size: str = "1 day") -> int:
    """把 fetch.historical_bars 的 DataFrame 写入，主键冲突时覆盖。返回行数。"""
    if df.empty:
        return 0
    rows = df.rename(columns={"barCount": "bar_count"}).reset_index().rename(columns={"date": "ts"})
    rows["symbol"], rows["bar_size"] = symbol.upper(), bar_size
    cols = ["symbol", "bar_size", "ts", "open", "high", "low", "close", "volume", "average", "bar_count"]
    rows = rows[[c for c in cols if c in rows.columns]]
    stmt = sa.text(
        f"insert into bars ({', '.join(rows.columns)}) values ({', '.join(':' + c for c in rows.columns)}) "
        "on conflict (symbol, bar_size, ts) do update set "
        + ", ".join(f"{c} = excluded.{c}" for c in rows.columns if c not in ("symbol", "bar_size", "ts"))
    )
    with engine.begin() as c:
        c.execute(stmt, rows.to_dict("records"))
    return len(rows)


def last_ts(symbol: str, bar_size: str = "1 day") -> pd.Timestamp | None:
    """该标的在库里的最后一根 K 线时间；没有数据返回 None。"""
    with engine.connect() as c:
        v = c.execute(sa.text("select max(ts) from bars where symbol = :s and bar_size = :b"),
                      {"s": symbol.upper(), "b": bar_size}).scalar()
    return pd.Timestamp(v) if v is not None else None


def read_bars(symbol: str, bar_size: str = "1 day", start=None, end=None) -> pd.DataFrame:
    q = "select ts, open, high, low, close, volume, average, bar_count from bars where symbol = :s and bar_size = :b"
    params = {"s": symbol.upper(), "b": bar_size}
    if start is not None:
        q += " and ts >= :start"; params["start"] = pd.Timestamp(start)
    if end is not None:
        q += " and ts <= :end"; params["end"] = pd.Timestamp(end)
    df = pd.read_sql(sa.text(q + " order by ts"), engine, params=params, index_col="ts")
    return df


def read_closes(symbols: list[str], bar_size: str = "1 day") -> pd.DataFrame:
    q = sa.text("select ts, symbol, close from bars where symbol = any(:syms) and bar_size = :b order by ts")
    df = pd.read_sql(q, engine, params={"syms": [s.upper() for s in symbols], "b": bar_size})
    return df.pivot(index="ts", columns="symbol", values="close")
