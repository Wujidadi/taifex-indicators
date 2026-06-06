# 台指期價量及技術指標分析計算工具 — 專案指引

## 概述

以 Python 撰寫的分析工具，從 TSV 檔案讀取台灣期貨交易所（TAIFEX）的 OHLCV 歷史資料，計算一組技術指標，並將結果輸出至 `analysis_results.tsv`。

## 建置與執行

```bash
# 初始設定：複製範例資料（核心流程無需 pip install）
cp data.example.tsv data.tsv

# 執行分析（預設：最近 120 個交易日）
python analysis

# 輸出所有資料
python analysis all

# 輸出最近 N 個交易日
python analysis 90
```

專案未提供 `requirements.txt`，相依套件為 `pandas` 與 `numpy`。程式碼刻意避免使用第三方技術分析函式庫，以維持 **Python 3.14 相容性**。

## 環境設定

> ⚠️ **重要**：本機使用 Homebrew 安裝的 Python 3（`/opt/homebrew/bin/python3`），需確保 pandas 和 numpy 已安裝。
>
> 執行 `python analysis` 時，請確認使用的 Python 版本有 pandas 和 numpy。若出現 `ModuleNotFoundError: No module named 'pandas'`，表示正在使用系統預設 Python（`/usr/bin/python3`），應改用 `/opt/homebrew/bin/python3 analysis` 或透過 alias 設定指向 Homebrew 版本。

## 架構

| 檔案                   | 用途                                                                      |
| ---------------------- | ------------------------------------------------------------------------- |
| `analysis`             | 單一進入點（無 `.py` 副檔名）；包含所有指標計算邏輯及命令列參數處理       |
| `data.tsv`             | 輸入資料——已列入 `.gitignore`，須以複製 `data.example.tsv` 的方式建立   |
| `data.example.tsv`     | 輸入範本：TSV 格式，包含欄位 `日期 開盤 最高 最低 收盤 成交量 是否結算日` |
| `analysis_results.tsv` | 輸出結果：寬表格式 TSV，所有指標欄位均使用繁體中文命名                    |
| `.env`                 | 存放 `FINMIND_API_TOKEN`，供選用的資料抓取功能使用                        |

## 輸入（原始）資料

- `data.tsv` / `data.example.tsv`\
  包含 1998 年 7 月 21 日台指期開市至 2026 年 3 月 27 日 13:45 收盤時的每日最近月臺股期貨資料\
  2001 年 4 月 6 日（星期五）以前為台指期（TX）的歷史資料\
  2001 年 4 月 9 日（星期一）起為小台指近月（MTX），當天小台指開市\
  因此 2001 年 4 月 6 日與 4 月 9 日兩個交易日的成交量有明顯斷層（6445 / 518），為正常現象。

## 技術指標

MA（5/10/20/60/120）、布林通道（22 日，±2σ）、CDP/AH/NH/NL/AL、拋物線 SAR、KD（9K/9D，EWM α=1/3）、MACD（DIF 12-26、訊號線 9、柱狀圖 OSC）、RSI（5/10）、DMI（+DI/-DI/ADX，14 日）。

## 開發慣例

- **Python 3.14 相容**：僅使用 `pandas`／`numpy`，禁止引入 `ta`、`ta-lib` 或類似套件。
- **主程式無副檔名**：執行方式為 `python analysis`，不得加上 `.py`。
- 欄位命名採「中文 → 英文」內部運算，輸出時再轉回繁體中文。
- 程式碼註解與終端輸出一律使用**繁體中文**。
- EditorConfig 規範：UTF-8 編碼、LF 換行、Python 縮排 4 格、JSON／YAML／MD 縮排 2 格。
- 輸入 TSV 的 `是否結算日` 欄位使用字串 `TRUE`／`FALSE`。

# Git Commit 指引

1. 所有 commit message 一律使用繁體中文（台灣），並採用台灣標準翻譯和慣用術語，不得夾雜除必要訊息外的日語、韓語或其他非中文詞彙（包含感嘆句、慣用語）。
2. 使用 [Conventional Commits](references/conventional-commits.md) 標準格式，以提高 commit message 的可讀性和可維護性。
3. 如果變動較多、較為複雜，應在 commit 標題之外，列出至少一項 bullet point，說明本次異動的摘要，以及各個檔案的異動原因。
4. Commit message 每個段落最後一句不要帶上句號，每個獨立行的最後面也不要帶句號。
5. 內容不遵照 72 字元斷行規則，而是以全域技能 /prose-linewrap 的規則為準。

## 專案內 Skills

- `mtx-daily-summary`：
  - 位置：`.github/skills/mtx-daily-summary/SKILL.md`
  - 用途：抓取 FinMind `TaiwanFuturesDaily` 的 MTX 當日資料，整併夜盤/日盤後輸出商品與價量摘要。
- `upsert-daily-data`：
  - 位置：`.github/skills/upsert-daily-data/SKILL.md`
  - 用途：呼叫 `src/finmind_mtx_daily_summary.py` 取得指定日期 OHLCV，判斷是否結算日，並將資料新增或更新至 `data.tsv`。
- `analysis`：
  - 位置：`.claude/skills/analysis/SKILL.md`
  - 用途：執行技術指標分析腳本，將結果輸出至 `analysis_results.tsv`；可指定輸出最近 N 個交易日或全部資料。
