#!/usr/bin/env python3

"""讀取 data/<id>.tsv 計算技術指標，將最近 N 個交易日（預設 120）的結果輸出至 reports/<id>.tsv"""

from __future__ import annotations

import sys
from pathlib import Path

# 以腳本所在的 src/ 目錄為匯入來源，使指標邏輯維持單一來源
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analysis import analyze_taifex_data

DEFAULT_DATA_ID = "MTX"
DEFAULT_DAYS = 120
DATA_DIR = Path("data")
REPORTS_DIR = Path("reports")


def _parse_args(argv: list[str]) -> tuple[str, int, bool]:
    """解析參數，回傳（data_id, days, output_all）

    'all'（不分大小寫）視為輸出全部；正整數視為交易日天數；其餘字串視為商品代碼
    """
    data_id = DEFAULT_DATA_ID
    days = DEFAULT_DAYS
    output_all = False

    for arg in argv:
        token = arg.strip()
        if not token:
            continue
        if token.lower() == "all":
            output_all = True
        elif token.isdigit():
            n = int(token)
            if n <= 0:
                print(f"警告：天數應為正整數，將使用預設值 {DEFAULT_DAYS}")
                n = DEFAULT_DAYS
            days = n
        else:
            data_id = token

    return data_id.upper(), days, output_all


def main() -> int:
    data_id, days, output_all = _parse_args(sys.argv[1:])

    input_path = DATA_DIR / f"{data_id.lower()}.tsv"
    if not input_path.exists():
        print(f"錯誤：找不到輸入資料 {input_path}")
        return 1

    result_df = analyze_taifex_data(str(input_path))

    if output_all:
        final_df = result_df
        print(f"分析完成！{data_id} 輸出全部資料（共 {len(final_df)} 筆）")
    else:
        final_df = result_df.tail(days)
        print(f"分析完成！{data_id} 輸出最近 {len(final_df)} 個交易日的資料")

    print("\n最新 5 筆資料預覽：")
    print(final_df.tail(5))

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"{data_id.lower()}.tsv"
    final_df.to_csv(output_path, sep="\t", index=False)
    print(f"\n完整結果已儲存至 {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
