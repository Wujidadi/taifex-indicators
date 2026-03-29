---
name: upsert-daily-data
description: 取得指定日期 MTX 的 OHLCV 資料，判斷是否結算日，並寫入（新增或更新）data.tsv
argument-hint: '<date: YYYY-MM-DD，可選，預設為台灣當日>'
user-invocable: true
---

<objective>
呼叫 `src/finmind_mtx_daily_summary.py` 腳本取得指定日期的 OHLCV 資料，判斷該日是否為當月第 3 個星期三（結算日），
並以 Tab 分隔的 7 欄格式將資料寫入 `data.tsv`：
- 若 `data.tsv` 已有相同日期的列，則更新該列。
- 若無相同日期，則按日期遞增順序插入至正確位置。
</objective>

<input>
- `date`（可選）：格式為 `YYYY-MM-DD`。
- 未提供時，以 `Asia/Taipei` 的當日日期作為查詢日期。
</input>

<rules>
- 結算日判斷規則：該日為當月第 3 個星期三，即 `weekday() == 2`（星期三）且日期落在 15～21 日之間。
- `data.tsv` 的欄位順序必須與標題列一致：`日期 開盤 最高 最低 收盤 成交量 是否結算日`，以 Tab 分隔。
- `是否結算日` 欄位使用字串 `TRUE` 或 `FALSE`（全大寫）。
- 不可更動 `data.tsv` 的標題列。
- OHLCV 資料透過呼叫 `src/finmind_mtx_daily_summary.py` 腳本取得，不在此 skill 內直接呼叫 FinMind API。
</rules>

<process>
1. 直接呼叫專案內可複用腳本：
   - 有帶 `date` 參數時：`python src/upsert_daily_data.py <date>`
   - 未帶 `date` 參數時：`python src/upsert_daily_data.py`

2. 腳本會自行完成以下流程：
   - 驗證 `date` 格式（`YYYY-MM-DD`）或套用 `Asia/Taipei` 當日日期。
   - 呼叫 `src/finmind_mtx_daily_summary.py` 子程序取得 OHLCV，解析其 stdout 6 行輸出。
   - 判斷目標日期是否為當月第 3 個星期三（結算日）。
   - 產生 7 欄 Tab 分隔的資料列。
   - 讀取 `data.tsv`，執行更新或依日期排序插入，再寫回。
   - 輸出操作結果（新增 / 更新）。

3. 將腳本 stdout 原樣回傳給使用者，不額外加工。
</process>

<implementation_hint>
腳本位置：`src/upsert_daily_data.py`

建議呼叫方式：

1. `python src/upsert_daily_data.py`
2. `python src/upsert_daily_data.py 2026-03-27`

注意事項：

- 腳本內部透過 `subprocess` 呼叫 `src/finmind_mtx_daily_summary.py`，需在專案根目錄執行。
- `data.tsv` 不存在時，腳本會自動建立並寫入標題列與第一筆資料。
- 若 `src/finmind_mtx_daily_summary.py` 回傳錯誤（例如非交易日、API 失敗），腳本會原樣印出錯誤並以非零碼退出，不修改 `data.tsv`。
</implementation_hint>
