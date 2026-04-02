---
name: mtx-daily-summary
description: 取得 MTX 當日夜盤與日盤資料並整併輸出指定價量欄位
argument-hint: '<date: YYYY-MM-DD，可選，預設為台灣當日>'
user-invocable: true
---

<objective>
呼叫 FinMind API 取得 MTX 當日資料，僅保留 contract_date 為 6 碼的商品月份，選出 ASCII 正序最前者，
以該月份的夜盤（after_market）與日盤（position）兩筆資料計算整併後的開高低收與成交量，
最後以固定繁體中文格式輸出。

若指定日期為星期四，腳本會在同一次 API 請求中一併取得前一交易日的資料，
比較兩日的 contract_date 以判斷前一天是否為結算日，並在標準 6 行之後額外輸出 2 行。
</objective>

<input>
- `date`（可選）：格式為 `YYYY-MM-DD`。
- `check_prev`（可選）：傳入 `true` 或 `yes`（不分大小寫）時，即使指定日期不是星期四，也強制抓取前一交易日資料以判斷前一天是否為結算日。
- 未提供 `date` 時，必須以 `Asia/Taipei` 的目前日期作為查詢日期。
</input>

<rules>
- API：`GET https://api.finmindtrade.com/api/v4/data`
- Query 參數：
  - `dataset=TaiwanFuturesDaily`
  - `data_id=MTX`
  - `end_date=<target_date>`（固定）
  - `start_date`：
    - 若 target_date **不是**星期四：`start_date=<target_date>`
    - 若 target_date **是**星期四：`start_date=<前一天>`，若該日無資料則再往前一天，直到取得前一交易日資料為止（最多往前 14 天）
- Header 必須帶：`Authorization: Bearer <FINMIND_API_TOKEN>`
- `FINMIND_API_TOKEN` 必須由工作區 `.env` 讀取，不可硬編碼，不可輸出到回覆內容。
- 不可在輸出中洩漏原始 token 或完整原始 JSON。
- 收盤價取自非零的 `settlement_price`（日結算價），`position` 優先，其次 `after_market`；兩者均為 0 則使用 `position.close`。
- 若能取得 `after_market` 但無 `position`（整盤尚未結束），直接以 `after_market` 的 OHLCV 作為當日資料輸出，不視為錯誤。
- 若連 `after_market` 都無法取得，則輸出錯誤訊息。
</rules>

<process>
1. 直接呼叫專案內可複用腳本：
   - 有帶 `date` 參數時：`python src/finmind_mtx_daily_summary.py <date>`
   - 未帶 `date` 參數時：`python src/finmind_mtx_daily_summary.py`
   - 額外強制抓取前一交易日時：`python src/finmind_mtx_daily_summary.py <date> yes`

2. 腳本會自行完成以下流程：
   - 驗證 `date` 格式（`YYYY-MM-DD`）或套用 `Asia/Taipei` 當日日期。
   - 從 `.env` 讀取 `FINMIND_API_TOKEN`，並以 `Authorization: Bearer` 呼叫 FinMind API。
   - 僅保留 `contract_date` 為 6 碼資料，取 ASCII 最小者。
   - 取得該商品 `after_market` 與 `position` 各一筆；收盤價優先採用非零 `settlement_price`。
   - 計算整併後開高低收與成交量，輸出固定 6 行摘要。
   - 若指定日期為星期四，額外輸出 `前日:` 與 `前日結算日:` 兩行。
   - 若發生錯誤，輸出對應錯誤訊息。

3. 將腳本 stdout 原樣回傳給使用者，不額外加工。
</process>

<implementation_hint>
腳本位置：`src/finmind_mtx_daily_summary.py`

建議呼叫方式：

1. `python src/finmind_mtx_daily_summary.py`
2. `python src/finmind_mtx_daily_summary.py 2026-03-27`
3. `python src/finmind_mtx_daily_summary.py 2026-03-27 yes`  ← 強制抓前一交易日

注意事項：

- 回覆以腳本輸出為準，不要重組欄位順序或文案。
- 不可輸出 token，不可回傳完整原始 JSON。
- 指定日期為星期四時，標準 6 行後會額外輸出：
  ```
  前日: YYYY-MM-DD
  前日結算日: TRUE|FALSE
  ```
</implementation_hint>
