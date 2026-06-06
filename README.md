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

## 補充分析

```bash
# 歷史急殺後報酬與回補時程回測（讀 data/<id>.tsv，輸出統計至終端）
python3 src/crash_recovery_backtest.py            # 預設 MTX、多門檻
python3 src/crash_recovery_backtest.py tx -6      # 指定商品與單日跌幅門檻
```

> 專題分析報告（非制式報表）置於 `reports/analysis/`。
