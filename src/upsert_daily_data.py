#!/usr/bin/env python3

"""呼叫 finmind_mtx_daily_summary.py 取得指定日期 MTX 資料，並寫入（新增或更新）data.tsv。"""

from __future__ import annotations

import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DATA_TSV = Path("data.tsv")
HEADER = "日期\t開盤\t最高\t最低\t收盤\t成交量\t是否結算日"


def _resolve_target_date(cli_date: str | None) -> str:
    """決定查詢日期：優先使用參數，否則取台灣當日。"""
    if cli_date:
        try:
            datetime.strptime(cli_date, "%Y-%m-%d")
        except ValueError:
            print("錯誤：date 參數格式錯誤，需為 YYYY-MM-DD。")
            raise SystemExit(1)
        return cli_date

    return datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d")


def _is_settlement_day(d: date) -> bool:
    """判斷是否為當月第 3 個星期三（結算日）。"""
    # 星期三：weekday() == 2；第 3 個星期三：日期落在第 15 至 21 日
    return d.weekday() == 2 and 15 <= d.day <= 21


def _fetch_ohlcv(target_date: str) -> tuple[int, int, int, int, int]:
    """呼叫 finmind_mtx_daily_summary.py 取得 OHLCV，解析並回傳。"""
    result = subprocess.run(
        [sys.executable, "src/finmind_mtx_daily_summary.py", target_date],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    output = result.stdout.strip()
    if not output:
        stderr = result.stderr.strip()
        print(f"錯誤：無法取得資料。{('  ' + stderr) if stderr else ''}")
        raise SystemExit(1)

    # 解析 6 行輸出：商品/開盤價/最高價/最低價/收盤價/成交量
    fields: dict[str, str] = {}
    for line in output.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()

    # 腳本若輸出錯誤訊息會以「錯誤：」開頭
    if "錯誤" in output or "開盤價" not in fields:
        print(output)
        raise SystemExit(1)

    try:
        open_price = int(fields["開盤價"])
        high_price = int(fields["最高價"])
        low_price  = int(fields["最低價"])
        close_price = int(fields["收盤價"])
        volume = int(fields["成交量"])
    except (KeyError, ValueError) as exc:
        print(f"錯誤：解析腳本輸出失敗（{exc}）。")
        raise SystemExit(1)

    return open_price, high_price, low_price, close_price, volume


def _build_tsv_line(
    target_date: str,
    open_price: int,
    high_price: int,
    low_price: int,
    close_price: int,
    volume: int,
    settlement: bool,
) -> str:
    settlement_str = "TRUE" if settlement else "FALSE"
    return f"{target_date}\t{open_price}\t{high_price}\t{low_price}\t{close_price}\t{volume}\t{settlement_str}"


def _update_data_tsv(target_date: str, new_line: str) -> None:
    """將 new_line 寫入 data.tsv：有相同日期則更新，否則依日期順序插入。"""
    if not DATA_TSV.exists():
        DATA_TSV.write_text(f"{HEADER}\n{new_line}\n", encoding="utf-8")
        print(f"已建立 {DATA_TSV} 並寫入 {target_date} 的資料。")
        return

    with DATA_TSV.open("r", encoding="utf-8", newline="") as fh:
        raw_lines = fh.read().splitlines(keepends=False)

    if not raw_lines:
        DATA_TSV.write_text(f"{HEADER}\n{new_line}\n", encoding="utf-8")
        print(f"已寫入 {target_date} 的資料。")
        return

    header_line = raw_lines[0]
    data_lines = raw_lines[1:]  # 不含標題列的資料行

    updated = False
    for idx, line in enumerate(data_lines):
        parts = line.split("\t")
        if not parts:
            continue
        existing_date = parts[0]
        if existing_date == target_date:
            data_lines[idx] = new_line
            updated = True
            break

    if not updated:
        # 找出正確插入位置以維持日期遞增順序
        insert_pos = len(data_lines)
        for idx, line in enumerate(data_lines):
            parts = line.split("\t")
            if parts and parts[0] > target_date:
                insert_pos = idx
                break
        data_lines.insert(insert_pos, new_line)

    new_content = "\n".join([header_line] + data_lines) + "\n"
    DATA_TSV.write_text(new_content, encoding="utf-8")

    action = "更新" if updated else "新增"
    print(f"已{action} {target_date} 的資料至 {DATA_TSV}。")


def main() -> int:
    arg_date = sys.argv[1] if len(sys.argv) > 1 else None
    target_date = _resolve_target_date(arg_date)

    d = date.fromisoformat(target_date)
    settlement = _is_settlement_day(d)

    open_price, high_price, low_price, close_price, volume = _fetch_ohlcv(target_date)

    new_line = _build_tsv_line(
        target_date, open_price, high_price, low_price, close_price, volume, settlement
    )

    print(f"資料：{new_line}")
    _update_data_tsv(target_date, new_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
