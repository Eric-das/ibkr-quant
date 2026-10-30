"""第一步：确认能连上 TWS。  用法：python scripts/test_connection.py"""
from ibkr_quant.config import IBConn
from ibkr_quant.ibkr_client import ib_session


def main() -> None:
    c = IBConn()
    print(f"连接 {c.host}:{c.port} clientId={c.client_id} ...")
    with ib_session(c) as ib:
        print("已连接，服务器版本:", ib.client.serverVersion())
        print("账户:", ib.managedAccounts())
        acct = ib.accountSummary()
        for item in acct:
            if item.tag in ("NetLiquidation", "TotalCashValue", "BuyingPower"):
                print(f"  {item.tag}: {item.value} {item.currency}")


if __name__ == "__main__":
    main()
