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
</objective>

<input>
- `date`（可選）：格式為 `YYYY-MM-DD`。
- 未提供 `date` 時，必須以 `Asia/Taipei` 的目前日期作為查詢日期。
</input>

<rules>
- API：`GET https://api.finmindtrade.com/api/v4/data`
- Query 參數固定：
  - `dataset=TaiwanFuturesDaily`
  - `data_id=MTX`
  - `start_date=<target_date>`
  - `end_date=<target_date>`
- Header 必須帶：`Authorization: Bearer <FINMIND_API_TOKEN>`
- `FINMIND_API_TOKEN` 必須由工作區 `.env` 讀取，不可硬編碼，不可輸出到回覆內容。
- 不可在輸出中洩漏原始 token 或完整原始 JSON。
</rules>

<process>
1. 直接呼叫專案內可複用腳本：
   - 有帶 `date` 參數時：`python src/finmind_mtx_daily_summary.py <date>`
   - 未帶 `date` 參數時：`python src/finmind_mtx_daily_summary.py`

2. 腳本會自行完成以下流程：
   - 驗證 `date` 格式（`YYYY-MM-DD`）或套用 `Asia/Taipei` 當日日期。
   - 從 `.env` 讀取 `FINMIND_API_TOKEN`，並以 `Authorization: Bearer` 呼叫 FinMind API。
   - 僅保留 `contract_date` 為 6 碼資料，取 ASCII 最小者。
   - 取得該商品 `after_market` 與 `position` 各一筆，計算整併後開高低收與成交量。
   - 依規定輸出 6 行摘要，或輸出對應錯誤訊息。

3. 將腳本 stdout 原樣回傳給使用者，不額外加工。
   </process>

<implementation_hint>
腳本位置：`src/finmind_mtx_daily_summary.py`

建議呼叫方式：

1. `python src/finmind_mtx_daily_summary.py`
2. `python src/finmind_mtx_daily_summary.py 2026-03-27`

注意事項：

- 回覆以腳本輸出為準，不要重組欄位順序或文案。
- 不可輸出 token，不可回傳完整原始 JSON。
  </implementation_hint>
