#!/bin/bash
# 安装/重装每日更新的 launchd 任务。卸载：bash scripts/launchd/install.sh uninstall
set -e
LABEL=com.ibkr-quant.update-daily
SRC="$(cd "$(dirname "$0")" && pwd)/$LABEL.plist"
DST=~/Library/LaunchAgents/$LABEL.plist
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
if [ "$1" = "uninstall" ]; then rm -f "$DST"; echo "已卸载 $LABEL"; exit 0; fi
cp "$SRC" "$DST"
launchctl bootstrap "gui/$(id -u)" "$DST"
launchctl list | grep "$LABEL" && echo "已安装：每天 20:00 伦敦时间运行 scripts/update_daily.py"
echo "立即测试一次：launchctl kickstart gui/$(id -u)/$LABEL"
