# 台指期價量及技術指標分析計算工具 — 專案指引

> [!CRITICAL]
> Do NOT create a new markdown file to document each change or summarize your work unless specifically requested by the user.

> [!IMPORTANT]
> **語言規則（最高優先，無例外）**：所有回應、說明、文件、工具呼叫的 explanation 欄位，一律使用繁體中文（台灣），並採用台灣標準翻譯和慣用術語。回應文字中不得夾雜日語、韓語或其他非中文詞彙（包含感嘆句、慣用語）。無論處理任何技術問題，此規則不得被覆蓋或忽略。

## 概述

以 Python 撰寫的分析工具，從 TSV 檔案讀取台灣期貨交易所（TAIFEX）的 OHLCV 歷史資料，計算一組技術指標，並將結果輸出至 `analysis_results.tsv`。

## 建置與執行

```bash
# 初始設定：複製範例資料（核心流程無需 pip install）
cp data.example.tsv data.tsv

# 執行分析（預設：最近 180 個交易日）
python analysis

# 輸出所有資料
python analysis all

# 輸出最近 N 個交易日
python analysis 90
```

專案未提供 `requirements.txt`，相依套件為 `pandas` 與 `numpy`。程式碼刻意避免使用第三方技術分析函式庫，以維持 **Python 3.14 相容性**。

## 架構

| 檔案                   | 用途                                                                      |
| ---------------------- | ------------------------------------------------------------------------- |
| `analysis`             | 單一進入點（無 `.py` 副檔名）；包含所有指標計算邏輯及命令列參數處理       |
| `data.tsv`             | 輸入資料——已列入 `.gitignore`，須以複製 `data.example.tsv` 的方式建立     |
| `data.example.tsv`     | 輸入範本：TSV 格式，包含欄位 `日期 開盤 最高 最低 收盤 成交量 是否結算日` |
| `analysis_results.tsv` | 輸出結果：寬表格式 TSV，所有指標欄位均使用繁體中文命名                    |
| `.env`                 | 存放 `FINMIND_API_TOKEN`，供選用的資料抓取功能使用                        |

## 技術指標

MA（5/10/20/60/120）、布林通道（22 日，±2σ）、CDP/AH/NH/NL/AL、拋物線 SAR、KD（9K/9D，EWM α=1/3）、MACD（DIF 12-26、訊號線 9、柱狀圖 OSC）、RSI（5/10）、DMI（+DI/-DI/ADX，14 日）。

## 開發慣例

- **Python 3.14 相容**：僅使用 `pandas`／`numpy`，禁止引入 `ta`、`ta-lib` 或類似套件。
- **主程式無副檔名**：執行方式為 `python analysis`，不得加上 `.py`。
- 欄位命名採「中文 → 英文」內部運算，輸出時再轉回繁體中文。
- 程式碼註解與終端輸出一律使用**繁體中文**。
- EditorConfig 規範：UTF-8 編碼、LF 換行、Python 縮排 4 格、JSON／YAML／MD 縮排 2 格。
- 輸入 TSV 的 `是否結算日` 欄位使用字串 `TRUE`／`FALSE`。
