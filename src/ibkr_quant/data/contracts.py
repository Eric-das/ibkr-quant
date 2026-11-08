"""合约解析：优先用 config/contracts.yaml 里缓存的 conId，避免每次都 qualifyContracts。

TWS 的合约定义服务器（secdef farm）掉线时 qualifyContracts 会永远不返回（2026-11-08 发现），
而带 conId 的历史数据请求不受影响，所以：有缓存就直接用，没缓存才带超时去查，查到后写回缓存。
"""
from __future__ import annotations

import asyncio

import yaml
from ib_async import IB, Stock

from ..config import PROJECT_ROOT

CACHE = PROJECT_ROOT / "config" / "contracts.yaml"


def _load() -> dict[str, int]:
    if CACHE.exists():
        return {k.upper(): int(v) for k, v in (yaml.safe_load(CACHE.read_text()) or {}).items()}
    return {}


def _save(cache: dict[str, int]) -> None:
    CACHE.write_text("# symbol -> IBKR conId，由 data/contracts.py 自动维护\n"
                     + yaml.safe_dump(dict(sorted(cache.items())), sort_keys=False))


def resolve(ib: IB, symbol: str, timeout: float = 20) -> Stock:
    """返回可直接用于 reqHistoricalData 的 Stock。缓存未命中且 timeout 秒内查不到会抛 TimeoutError。"""
    symbol = symbol.upper()
    cache = _load()
    if symbol in cache:
        return Stock(symbol, "SMART", "USD", conId=cache[symbol])
    con = Stock(symbol, "SMART", "USD")
    ib.run(asyncio.wait_for(ib.qualifyContractsAsync(con), timeout))
    if not con.conId:
        raise ValueError(f"{symbol}: qualifyContracts 没返回 conId")
    cache[symbol] = con.conId
    _save(cache)
    return con
