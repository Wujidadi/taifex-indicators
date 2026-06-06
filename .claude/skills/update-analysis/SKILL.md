---
name: update-analysis
description: 抓取指定期貨商品在日期區間的每日資料寫入 data/<id>.tsv，再產生最近 N 日技術指標分析至 reports/<id>.tsv
argument-hint: "<data_id: 可選，預設 MTX> <start_date: YYYY-MM-DD，可選，預設台灣當日> <end_date: 可選，預設同起日> <days: 可選，預設 120；傳入 all 則輸出全部>"
user-invocable: true
---

<objective>
以兩支專案內可複用腳本，一次完成指定商品的「資料更新」與「指標分析」：

1. 呼叫 `src/finmind_futures_daily.py`，查詢 FinMind `TaiwanFuturesDaily` 指定商品於日期區間的每日 OHLCV，整併夜盤／日盤後寫入（新增或更新）`data/<id>.tsv`（`<id>` 為商品代碼小寫）。
2. 呼叫 `src/analyze_futures.py`，讀取 `data/<id>.tsv`，計算技術指標並將最近 N 個交易日的結果輸出至 `reports/<id>.tsv`。
   </objective>

<input>
- `data_id`（可選）：期貨商品代碼，例如 `MTX`（小台指）、`TX`（台指期）、`TMF`（微台指）。未提供時預設 `MTX`。大小寫不拘，內部統一轉大寫呼叫 API、小寫作為檔名。
- `start_date` / `end_date`（可選）：格式 `YYYY-MM-DD`。未提供時以 `Asia/Taipei` 當日作為查詢日期，且訖日預設與起日相同（即只查當天）。
- `days`（可選）：分析時輸出最近幾個交易日，正整數；傳入 `all` 則輸出全部。未提供時預設 `120`。
</input>

<rules>
- 資料檔命名為 `data/<id>.tsv`、分析報表命名為 `reports/<id>.tsv`，`<id>` 一律為商品代碼小寫（例如 MTX → `data/mtx.tsv`、`reports/mtx.tsv`）。
- 結算日判斷沿用專案慣例：當月第 3 個星期三（`weekday() == 2` 且日期落在 15～21 日），由抓取腳本逐日寫入 `是否結算日` 欄位（`TRUE`／`FALSE`）。遇國定假日順延的特例不在此規則涵蓋範圍。
- 不在 skill 內直接呼叫 FinMind API 或重寫指標邏輯，一律透過上述兩支腳本完成，以避免重複探索與額外成本。
- 兩支腳本均須在專案根目錄執行。
</rules>

<process>
1. 由使用者輸入解析出 `data_id`、`start_date`、`end_date`、`days`，未提供者套用上述預設值。

2. 先執行資料更新（日期與商品代碼皆為位置參數，順序不拘，符合 `YYYY-MM-DD` 者視為日期，其餘視為商品代碼）：
   - 預設（當日、MTX）：`python3 src/finmind_futures_daily.py`
   - 指定區間：`python3 src/finmind_futures_daily.py <start_date> <end_date>`
   - 指定商品與區間：`python3 src/finmind_futures_daily.py <data_id> <start_date> <end_date>`

3. 再執行指標分析（`all` 或正整數視為天數，其餘視為商品代碼）：
   - 預設（MTX、120 日）：`python3 src/analyze_futures.py`
   - 指定商品與天數：`python3 src/analyze_futures.py <data_id> <days>`
   - 輸出全部：`python3 src/analyze_futures.py <data_id> all`

4. 將兩支腳本的 stdout 原樣回傳給使用者，不額外加工。

5. 若步驟 2 顯示「查無資料」（非交易日或當日尚未有資料），可僅回報該訊息；惟仍可續跑步驟 3，以既有 `data/<id>.tsv` 產生分析報表。
   </process>

<implementation_hint>
腳本位置：

- `src/finmind_futures_daily.py`：抓取並 upsert 至 `data/<id>.tsv`，由已歸檔的 `archive/src/finmind_mtx_daily_summary.py` 整併邏輯一般化而來（支援任一商品與日期區間）。
- `src/analyze_futures.py`：匯入 `src/analysis.py` 的 `analyze_taifex_data` 計算指標，輸出至 `reports/<id>.tsv`，使指標邏輯維持單一來源。

呼叫範例（以小台指 MTX 為例）：

1. `python3 src/finmind_futures_daily.py 2026-06-01 2026-06-05` ← 補抓區間資料至 data/mtx.tsv
2. `python3 src/analyze_futures.py 120` ← 產生最近 120 日報表至 reports/mtx.tsv
3. `python3 src/finmind_futures_daily.py TX 2026-06-03` ← 抓台指期單日至 data/tx.tsv
4. `python3 src/analyze_futures.py TX all` ← 台指期全部資料報表至 reports/tx.tsv

注意事項：

- 需在 `.env` 設定 `FINMIND_API_TOKEN`；缺少時抓取腳本會印出錯誤並以非零碼退出，不修改 `data/<id>.tsv`。
- 本機請使用具備 pandas／numpy 的 Homebrew Python 3（`/opt/homebrew/bin/python3`）；若 `python3` 即指向該版本則可直接使用。
- 抓取腳本僅取得夜盤（日盤尚未結束）時，仍以夜盤資料寫入，待日盤就緒後重跑即可更新。
- `data/<id>.tsv` 與 `reports/<id>.tsv` 不存在時，腳本會自動建立。
  </implementation_hint>
