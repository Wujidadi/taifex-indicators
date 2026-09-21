# 台指期價量及技術指標分析計算工具

## Quick Start

```bash
# 複製環境設定，並填入 FINMIND_API_TOKEN
cp .env.example .env

# 1. 抓取資料：查詢指定商品（預設 MTX）並寫入 data/<id>.tsv
python3 src/finmind_futures_daily.py                         # 預設 MTX、台灣當日
python3 src/finmind_futures_daily.py 2026-06-01 2026-06-05   # 指定區間
python3 src/finmind_futures_daily.py TX 2026-06-03           # 指定商品、單日

# 2. 產生報表：讀 data/<id>.tsv，輸出最近 N 日至 reports/<id>.tsv
python3 src/analyze_futures.py            # 預設 MTX、最近 120 日
python3 src/analyze_futures.py all        # MTX、全部資料
python3 src/analyze_futures.py 90         # MTX、最近 90 日
```

> 於 Claude Code 中亦可直接呼叫 `/update-analysis` 技能，一次完成抓取與分析。

## 排程（macOS）

`launchd/com.wujidadi.taifex.daily-update.plist` 於星期一至五 16:40（系統時區）執行 `src/daily_update.py`，將 TX、MTX、TMF 的資料補抓至台灣當日並重新產生報表，日誌寫入 `~/Library/Logs/taifex/daily-update.log`。
FinMind `TaiwanFuturesDaily` 於星期一至五 16:30 更新，排程時間依此保留 10 分鐘緩衝。

```bash
# 安裝或更新排程
mkdir -p ~/Library/Logs/taifex
cp launchd/com.wujidadi.taifex.daily-update.plist ~/Library/LaunchAgents/
launchctl bootout gui/$(id -u)/com.wujidadi.taifex.daily-update 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.wujidadi.taifex.daily-update.plist

# 立即試跑一次
launchctl kickstart gui/$(id -u)/com.wujidadi.taifex.daily-update
```

排程入口須為 Homebrew 的 Python：launchd 下的 `/bin/zsh` 無「文件」檔案夾的取用權限，無法開啟專案內的腳本。

## 補充分析

```bash
# 歷史急殺後報酬與回補時程回測（讀 data/<id>.tsv，輸出統計至終端）
python3 src/crash_recovery_backtest.py            # 預設 MTX、多門檻
python3 src/crash_recovery_backtest.py tx -6      # 指定商品與單日跌幅門檻
```

> 專題分析報告（非制式報表）置於 `reports/analysis/`。
