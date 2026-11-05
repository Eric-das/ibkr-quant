"""每日增量更新：只拉数据库里最后一根 K 线之后的部分，写入 Parquet + PostgreSQL。

用法：
    python scripts/update_daily.py              # settings.yaml 里的 default_universe
    python scripts/update_daily.py TSLA NVDA    # 指定代码（库里没有的会按 settings.history 做全量首拉）
    python scripts/update_daily.py --dry-run    # 只看每个标的需要补多少天，不连 TWS

前提：TWS 已登录。连不上时退出码 2，并写入 data/logs/update_daily.log。
由 launchd 每天定时调用，见 scripts/launchd/。
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone

import pandas as pd

from ibkr_quant.config import DATA_DIR, SETTINGS
from ibkr_quant.data.fetch import historical_bars, stock
from ibkr_quant.data.store import save_bars
from ibkr_quant.db import init_db, last_ts, upsert_bars
from ibkr_quant.ibkr_client import ib_session

LOG_DIR = DATA_DIR / "logs"
MAX_INCREMENTAL_DAYS = 300   # 落后超过这个天数就按 settings.history 全量重拉


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    log = logging.getLogger("update_daily")
    log.setLevel(logging.INFO)
    for h in (logging.FileHandler(LOG_DIR / "update_daily.log"), logging.StreamHandler(sys.stdout)):
        h.setFormatter(fmt)
        log.addHandler(h)
    return log


def plan_duration(symbol: str, bar_size: str) -> tuple[str, pd.Timestamp | None]:
    """返回 (IBKR durationStr, 库里最后时间)。多拉几天做重叠，upsert 会覆盖重复的。"""
    last = last_ts(symbol, bar_size)
    h = SETTINGS["history"]
    if last is None:
        return h["duration"], None
    gap = (pd.Timestamp.now(tz="UTC").normalize() - last.tz_convert("UTC").normalize()).days
    if gap > MAX_INCREMENTAL_DAYS:
        return h["duration"], last
    return f"{max(gap + 3, 5)} D", last


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="*", default=SETTINGS.get("default_universe", []))
    ap.add_argument("--bar", default=SETTINGS["history"].get("bar_size", "1 day"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    log = setup_logging()
    init_db()

    plan = {s: plan_duration(s, a.bar) for s in a.symbols}
    for s, (dur, last) in plan.items():
        log.info("%s: 库里最后 %s -> 请求 %s", s, last.date() if last is not None else "无", dur)
    if a.dry_run:
        return 0

    start = SETTINGS["history"].get("start")
    failed: list[str] = []
    try:
        ib_ctx = ib_session()
        ib = ib_ctx.__enter__()
    except Exception as e:  # noqa: BLE001
        log.error("连不上 TWS（%s），请确认 TWS 已登录且 API 已开启", e)
        return 2
    try:
        for s, (dur, last) in plan.items():
            try:
                con = stock(s)
                ib.qualifyContracts(con)
                df = historical_bars(ib, con, duration=dur, bar_size=a.bar)
                if start and not df.empty:
                    df = df[df.index >= pd.Timestamp(start)]
                if df.empty:
                    log.warning("%s: 没拿到数据", s)
                    failed.append(s)
                    continue
                save_bars(df, s, a.bar)
                n = upsert_bars(df, s, a.bar)
                new = df.index[-1].date()   # IBKR 返回 tz-naive，库里是 tz-aware，按日期比
                log.info("%s: 写入 %d 行，最新 %s%s", s, n, new,
                         "" if last is None or new > last.date() else "（无新数据）")
            except Exception as e:  # noqa: BLE001
                log.exception("%s: 失败 %s", s, e)
                failed.append(s)
    finally:
        ib_ctx.__exit__(None, None, None)

    if failed:
        log.error("失败标的: %s", ", ".join(failed))
        return 1
    log.info("全部完成 %s", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
