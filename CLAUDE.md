# 台指期價量及技術指標分析計算工具 — 專案指引

## 概述

以 Python 撰寫的分析工具，透過 FinMind API 抓取台灣期貨交易所（TAIFEX）各商品的每日 OHLCV 資料，計算一組技術指標。支援多商品：每個商品的原始資料存於 `data/<id>.tsv`、分析報表輸出至 `reports/<id>.tsv`（`<id>` 為商品代碼小寫，例如 MTX → `data/mtx.tsv`、`reports/mtx.tsv`）。

## 建置與執行

主流程（多商品）分兩步，可透過 `/update-analysis` 技能一次完成，或直接呼叫腳本：

```bash
# 1. 抓取資料：查詢指定商品（預設 MTX）日期區間並寫入 data/<id>.tsv
python3 src/finmind_futures_daily.py                         # 預設 MTX、台灣當日
python3 src/finmind_futures_daily.py 2026-06-01 2026-06-05   # MTX、指定區間
python3 src/finmind_futures_daily.py TX 2026-06-03           # 指定商品、單日

# 2. 產生報表：讀 data/<id>.tsv，輸出最近 N 日至 reports/<id>.tsv
python3 src/analyze_futures.py                               # 預設 MTX、最近 120 日
python3 src/analyze_futures.py 90                            # MTX、最近 90 日
python3 src/analyze_futures.py TX all                        # TX、全部資料
```

專案未提供 `requirements.txt`，相依套件為 `pandas` 與 `numpy`。程式碼刻意避免使用第三方技術分析函式庫，以維持 **Python 3.14 相容性**。

## 環境設定

> ⚠️ **重要**：本機使用 Homebrew 安裝的 Python 3（`/opt/homebrew/bin/python3`），需確保 pandas 和 numpy 已安裝。
>
> 執行腳本時，請確認使用的 Python 版本有 pandas 和 numpy。若出現 `ModuleNotFoundError: No module named 'pandas'`，表示正在使用系統預設 Python（`/usr/bin/python3`），應改用 `/opt/homebrew/bin/python3 src/analyze_futures.py` 或透過 alias 設定指向 Homebrew 版本。

## 架構

| 路徑／檔案                       | 用途                                                                                                                         |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `src/finmind_futures_daily.py`   | 抓取指定商品日期區間的每日 OHLCV，整併夜盤／日盤後寫入（upsert）`data/<id>.tsv`                                              |
| `src/analyze_futures.py`         | 讀取 `data/<id>.tsv` 計算技術指標，輸出最近 N 日結果至 `reports/<id>.tsv`（匯入 `src/analysis.py` 的計算函式，維持單一來源） |
| `src/analysis.py`                | 技術指標計算邏輯（`analyze_taifex_data`）；供 `analyze_futures.py` 匯入的單一來源                                            |
| `src/crash_recovery_backtest.py` | 歷史急殺後報酬與回補時程回測（讀 `data/<id>.tsv`，輸出統計至終端）；輔助分析工具，非主流程                                   |
| `data/<id>.tsv`                  | 各商品原始 OHLCV 資料，`<id>` 為商品代碼小寫（如 `data/tx.tsv`、`data/mtx.tsv`、`data/tmf.tsv`）                             |
| `reports/<id>.tsv`               | 各商品分析報表，寬表格式 TSV，所有指標欄位均使用繁體中文命名                                                                 |
| `reports/analysis/`              | 專題分析報告與輔助腳本輸出（如夜盤雪崩分析），與 `reports/<id>.tsv` 制式報表區隔；可持續追加                                 |
| `data.tsv`                       | 舊版單一商品輸入（根目錄存檔，已列入 `.gitignore`，本機為 iCloud 連結；已無對應執行腳本）                                    |
| `analysis_results.tsv`           | 舊版單一商品輸出（根目錄存檔，已列入 `.gitignore`；已無對應執行腳本）                                                        |
| `.env`                           | 存放 `FINMIND_API_TOKEN`，供資料抓取使用                                                                                     |
| `archive/`                       | 已歸檔的舊技能與後端腳本（`mtx-daily-summary`、`upsert-daily-data`、`analysis` 等）                                          |

## 輸入（原始）資料

- `data/<id>.tsv`：各商品每日最近月 OHLCV 資料，依商品分檔\
  `data/tx.tsv` 為台指期大台（TX），自 1998 年 7 月 21 日台指期開市起之完整歷史，涵蓋 2001 年小台上市後迄今（與 `mtx` 並存，非僅早期區段）\
  `data/mtx.tsv` 為小台指（MTX），自 2001 年 4 月 9 日（星期一）小台指開市起\
  `data/tmf.tsv` 為微型台指（TMF），FinMind 可得資料自 2024 年 7 月 29 日起\
  舊版根目錄 `data.tsv` 則為 TX（1998～2001）接續 MTX（2001 起）的單一序列，因此其 2001 年 4 月 6 日與 4 月 9 日兩個交易日的成交量有明顯斷層（6445 / 518），為正常現象

## 技術指標

MA（5/10/20/60/120）、布林通道（22 日，±2σ）、CDP/AH/NH/NL/AL、拋物線 SAR、KD（9K/9D，EWM α=1/3）、MACD（DIF 12-26、訊號線 9、柱狀圖 OSC）、RSI（5/10）、DMI（+DI/-DI/ADX，14 日）。

## 開發慣例

- **Python 3.14 相容**：僅使用 `pandas`／`numpy`，禁止引入 `ta`、`ta-lib` 或類似套件。
- 欄位命名採「中文 → 英文」內部運算，輸出時再轉回繁體中文。
- 程式碼註解與終端輸出一律使用**繁體中文**。
- EditorConfig 規範：UTF-8 編碼、LF 換行、Python 縮排 4 格、JSON／YAML／MD 縮排 2 格。
- Markdown 格式化：撰寫或修改 Markdown（本說明、報告、技能檔等）後，執行 `md-fmt <檔案或資料夾>` 進行格式化；僅當本地無 `md-fmt` 工具時，才改採替代方案（依本檔格式規範手動整理）。
- 輸入 TSV 的 `是否結算日` 欄位使用字串 `TRUE`／`FALSE`。
- 多商品資料與報表採 `data/<id>.tsv`／`reports/<id>.tsv` 命名，`<id>` 一律為商品代碼小寫。
- 結算日判斷沿用「當月第 3 個星期三」規則（`weekday() == 2` 且日期落在 15～21 日），由 `finmind_futures_daily.py` 逐日寫入；遇國定假日順延的特例不在此規則涵蓋範圍。
- 所有腳本集中於 `src/`；指標計算邏輯統一由 `src/analysis.py` 提供，為各分析腳本匯入的單一來源。

# Git Commit 指引

1. 所有 commit message 一律使用繁體中文（台灣），並採用台灣標準翻譯和慣用術語，不得夾雜除必要訊息外的日語、韓語或其他非中文詞彙（包含感嘆句、慣用語）。
2. 使用 [Conventional Commits](.claude/references/conventional-commits.md) 標準格式，以提高 commit message 的可讀性和可維護性。
3. 如果變動較多、較為複雜，應在 commit 標題之外，列出至少一項 bullet point，說明本次異動的摘要，以及各個檔案的異動原因。
4. Commit message 每個段落最後一句不要帶上句號，每個獨立行的最後面也不要帶句號。
5. 內容不遵照 72 字元斷行規則，而是以全域技能 /prose-linewrap 的規則為準。

## 專案內 Skills

- `update-analysis`：
  - 位置：`.claude/skills/update-analysis/SKILL.md`
  - 用途：抓取指定商品（預設 MTX）日期區間的每日資料寫入 `data/<id>.tsv`，再產生最近 N 日技術指標分析至 `reports/<id>.tsv`；透過 `src/finmind_futures_daily.py` 與 `src/analyze_futures.py` 兩支腳本完成。

> 舊技能 `mtx-daily-summary`、`upsert-daily-data`、`analysis` 及其後端腳本 `src/finmind_mtx_daily_summary.py`、`src/upsert_daily_data.py` 已歸檔至 `archive/`，由本技能與上述兩支腳本取代。
