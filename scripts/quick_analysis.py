"""用本地数据做一个最小分析：收益统计 + 净值图。  用法：python scripts/quick_analysis.py AAPL MSFT SPY"""
import sys

import matplotlib.pyplot as plt

from ibkr_quant.analysis.returns import simple_returns, summary
from ibkr_quant.config import PROCESSED_DIR, SETTINGS
from ibkr_quant.data.store import load_closes


def main() -> None:
    symbols = sys.argv[1:] or SETTINGS.get("default_universe", [])
    closes = load_closes(symbols).dropna()
    print(summary(closes).round(4))

    nav = (1 + simple_returns(closes)).cumprod()
    ax = nav.plot(title="Cumulative return (rebased to 1)", figsize=(10, 5))
    ax.grid(alpha=0.3)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / "nav.png"
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    print("图已保存:", out)


if __name__ == "__main__":
    main()
