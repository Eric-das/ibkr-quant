# ibkr-quant

数据分析项目，数据源 Interactive Brokers（TWS API），后续逐步扩展成量化研究/回测项目。

## 目录

```
config/settings.yaml       项目设置（股票池、K线周期、行情类型）
.env                       连接参数（host/port/clientId），不进 git
src/ibkr_quant/
  config.py                读取设置
  ibkr_client.py           连接 TWS 的 with ib_session() as ib
  data/fetch.py            拉历史 K 线 -> DataFrame
  data/store.py            Parquet 本地存储（data/raw/<bar>/<SYMBOL>.parquet）
  analysis/returns.py      收益、波动、Sharpe、最大回撤
scripts/
  test_connection.py       第一步：能不能连上
  fetch_history.py         首次全量拉数据
  update_daily.py          每日增量更新（只补库里最后一根 K 线之后的部分）
  launchd/                 每日定时任务（install.sh 安装）
  quick_analysis.py        用本地数据做最小分析并出图
notebooks/                 探索性分析用
tests/                     pytest
```

## 第一次使用

1. 激活环境：`source .venv/bin/activate`
2. 打开 TWS 并登录（建议先用 paper 账户）。
   TWS 菜单 File > Global Configuration > API > Settings：
   - 勾选 Enable ActiveX and Socket Clients
   - 勾选 Read-Only API（只读，防止代码误下单）
   - Socket port：paper 默认 7497，live 默认 7496，要和 `.env` 里 IB_PORT 一致
   - 取消 Allow connections from localhost only 不需要动，本机连接即可
3. `python scripts/test_connection.py`
4. `python scripts/fetch_history.py` 然后 `python scripts/quick_analysis.py`

## 注意

- 提交时 notebook 输出会被 nbstripout 自动清空（git filter），本地文件不受影响。
  新克隆的机器上要跑一次：`pip install -e ".[dev]" && nbstripout --install --attributes .gitattributes`

- 没有订阅实时行情时 `market_data_type: 3`（延迟数据）即可拉历史 K 线。
- IBKR 历史数据有节流（pacing）限制，大量拉取请控制频率、分段请求。
- 每个连接的 clientId 要唯一，Jupyter 和脚本同时连时改不同的 IB_CLIENT_ID。

## 每日更新

- 手动：`python scripts/update_daily.py`（`--dry-run` 只看需要补几天）。按库里 `max(ts)` 算要补的天数，多拉 3 天重叠，upsert 覆盖重复行；落后超过 300 天或库里没有的标的按 `settings.history` 全量重拉。
- 自动：`bash scripts/launchd/install.sh` 装成 launchd 任务，每天 20:00（伦敦时间）运行。此时美股还在盘中，当天那根 K 线先以快照写入，次日运行时自动被完整数据覆盖；Mac 当时在休眠的话下次唤醒时补跑。卸载加 `uninstall`。
- 前提是 **TWS 当时处于登录状态**，否则脚本记录错误后退出（退出码 2）。日志在 `data/logs/update_daily.log`。
- 改股票池：编辑 `config/settings.yaml` 的 `default_universe`，新标的下次运行时自动全量首拉。

## 下一步路线

数据层（多周期、增量更新、基本面/期权链） → 因子研究 → 回测框架 → paper 交易。

## 数据库（PostgreSQL 17，Homebrew）

- 本机 socket 连接、无密码，库名 `ibkr_quant`，连接串在 `.env` 的 `DATABASE_URL`。
- 表 `bars(symbol, bar_size, ts, open, high, low, close, volume, average, bar_count)`，主键 (symbol, bar_size, ts)。
- `src/ibkr_quant/db.py`：`init_db()` 建表，`upsert_bars(df, symbol, bar)` 写入（重复覆盖），`read_bars()` / `read_closes()` 读取。
- `python scripts/load_parquet_to_db.py` 把 data/raw 的 Parquet 全部灌进库。
- 设为开机自启：`brew services start postgresql@17`；命令行工具加进 PATH：
  `echo 'export PATH="/opt/homebrew/opt/postgresql@17/bin:$PATH"' >> ~/.zshrc`
- 分层：Parquet 是原始落地层，PostgreSQL 是查询/研究层。
