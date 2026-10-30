"""与 TWS / IB Gateway 的连接。用法：

    with ib_session() as ib:
        ...

前提：TWS 已登录，且 Global Configuration > API > Settings 里勾选了
"Enable ActiveX and Socket Clients"，端口和 .env 里的 IB_PORT 一致。
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from ib_async import IB

from .config import SETTINGS, IBConn


def connect(conn: IBConn | None = None, timeout: float = 10, readonly: bool = True) -> IB:
    """readonly=True：只拉数据，不请求订单，也不会下单。以后要交易再显式传 False。"""
    conn = conn or IBConn()
    ib = IB()
    ib.connect(conn.host, conn.port, clientId=conn.client_id, timeout=timeout, readonly=readonly)
    ib.reqMarketDataType(int(SETTINGS.get("market_data_type", 3)))
    return ib


@contextmanager
def ib_session(conn: IBConn | None = None) -> Iterator[IB]:
    ib = connect(conn)
    try:
        yield ib
    finally:
        ib.disconnect()
