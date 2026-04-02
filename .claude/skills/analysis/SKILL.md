---
name: analysis
description: 執行技術指標分析，將結果輸出至 analysis_results.tsv
argument-hint: "<days: 正整數，可選，預設輸出最近 120 個交易日；傳入 all 則輸出全部資料>"
user-invocable: true
---

<objective>
呼叫專案根目錄的 `analysis` 腳本，對 `data.tsv` 計算技術指標，並將結果輸出至 `analysis_results.tsv`。
</objective>

<input>
- `days`（可選）：
  - 正整數：輸出最近 N 個交易日的分析結果。
  - `all`：輸出全部資料。
  - 未提供：預設輸出最近 120 個交易日。
</input>

<process>
1. 依照是否有 `days` 參數選擇呼叫方式：
   - 有帶 `days` 參數時：`python3 analysis <days>`
   - 未帶 `days` 參數時：`python3 analysis`

2. 將腳本 stdout 原樣回傳給使用者，不額外加工。
</process>

<implementation_hint>
腳本位置：專案根目錄的 `analysis`（無副檔名）

呼叫範例：

1. `python3 analysis` ← 最近 180 個交易日
2. `python3 analysis 20` ← 最近 20 個交易日
3. `python3 analysis all` ← 全部資料

注意事項：

- 須在專案根目錄執行。
- 輸入資料來源為 `data.tsv`，輸出結果寫入 `analysis_results.tsv`。
</implementation_hint>
