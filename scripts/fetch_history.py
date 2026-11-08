"""拉取历史 K 线，存到 data/raw（Parquet）并写入 PostgreSQL bars 表。

用法：
    python scripts/fetch_history.py                              # settings.yaml 里的 default_universe
    python scripts/fetch_history.py TSLA NVDA                    # 指定代码
    python scripts/fetch_history.py SPY --start 2019-01-01 --duration "8 Y" --bar "1 day"
    python scripts/fetch_history.py SPY --no-db                  # 只存 Parquet
"""
import argparse

import pandas as pd

from ibkr_quant.config import SETTINGS
from ibkr_quant.data.contracts import resolve
from ibkr_quant.data.fetch import historical_bars
from ibkr_quant.data.store import save_bars
from ibkr_quant.ibkr_client import ib_session


def main() -> None:
    h = SETTINGS["history"]
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="*", default=SETTINGS.get("default_universe", []))
    ap.add_argument("--duration", default=h.get("duration"))
    ap.add_argument("--bar", default=h.get("bar_size", "1 day"))
    ap.add_argument("--start", default=h.get("start"), help="只保留 >= 此日期的数据，如 2019-01-01")
    ap.add_argument("--no-db", action="store_true", help="不写 PostgreSQL")
    a = ap.parse_args()

    if not a.no_db:
        from ibkr_quant.db import init_db, upsert_bars
        init_db()

    with ib_session() as ib:
        for sym in a.symbols:
            con = resolve(ib, sym)
            df = historical_bars(ib, con, duration=a.duration, bar_size=a.bar)
            if a.start and not df.empty:
                df = df[df.index >= pd.Timestamp(a.start)]
            if df.empty:
                print(f"{sym}: 没拿到数据")
                continue
            save_bars(df, sym, a.bar)
            n_db = upsert_bars(df, sym, a.bar) if not a.no_db else 0
            print(f"{sym}: {len(df)} 根 {a.bar}  {df.index[0].date()} ~ {df.index[-1].date()}"
                  + ("" if a.no_db else f"  -> 数据库 {n_db} 行"))


if __name__ == "__main__":
    main()
