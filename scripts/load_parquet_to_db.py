"""把 data/raw 里已有的 Parquet 全部灌进 PostgreSQL。  用法：python scripts/load_parquet_to_db.py"""
import pandas as pd

from ibkr_quant.config import RAW_DIR
from ibkr_quant.db import init_db, upsert_bars


def main() -> None:
    init_db()
    for p in sorted(RAW_DIR.glob("*/*.parquet")):
        bar = p.parent.name.replace("_", " ")
        n = upsert_bars(pd.read_parquet(p), p.stem, bar)
        print(f"{p.stem} ({bar}): {n} 行")


if __name__ == "__main__":
    main()
