#!/usr/bin/env python3

"""取得 MTX 當日夜盤/日盤整併後的價量摘要。"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo


def _load_finmind_token() -> str:
    """優先讀取環境變數，若無則從 .env 載入 FINMIND_API_TOKEN。"""
    token = os.getenv("FINMIND_API_TOKEN", "").strip()
    if token:
        return token

    try:
        with open(".env", "r", encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                if key.strip() == "FINMIND_API_TOKEN":
                    return value.strip().strip('"').strip("'")
    except FileNotFoundError:
        return ""

    return ""


def _resolve_target_date(cli_date: str | None) -> str:
    """決定查詢日期：優先使用參數，否則取台灣當日。"""
    if cli_date:
        try:
            datetime.strptime(cli_date, "%Y-%m-%d")
        except ValueError:
            print("錯誤：date 參數格式錯誤，需為 YYYY-MM-DD。")
            raise SystemExit(0)
        return cli_date

    return datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d")


def _request_finmind_data(token: str, target_date: str) -> list[dict]:
    params = {
        "dataset": "TaiwanFuturesDaily",
        "data_id": "MTX",
        "start_date": target_date,
        "end_date": target_date,
    }
    query = urllib.parse.urlencode(params)
    url = f"https://api.finmindtrade.com/api/v4/data?{query}"
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        print("錯誤：FinMind API 請求失敗。")
        raise SystemExit(0)

    if payload.get("status") != 200:
        print("錯誤：FinMind API 請求失敗。")
        raise SystemExit(0)

    data = payload.get("data") or []
    if not data:
        print("錯誤：指定日期查無 MTX 資料。")
        raise SystemExit(0)

    return data


def _to_int_price(value: int | float) -> int:
    return int(float(value))


def _calculate_summary(data: list[dict], target_date: str) -> tuple[str, int, int, int, int, int]:
    filtered_by_date = [
        item for item in data if isinstance(item.get("date"), str) and item.get("date") == target_date
    ]
    if not filtered_by_date:
        print("錯誤：指定日期查無 MTX 資料。")
        raise SystemExit(0)

    six_digit_contracts = [
        item
        for item in filtered_by_date
        if isinstance(item.get("contract_date"), str) and len(item["contract_date"]) == 6
    ]
    if not six_digit_contracts:
        print("錯誤：查無符合條件的 6 碼到期月份資料。")
        raise SystemExit(0)

    contract_date = min(item["contract_date"] for item in six_digit_contracts)

    after_market_rows = [
        item
        for item in six_digit_contracts
        if item.get("contract_date") == contract_date
        and item.get("trading_session") == "after_market"
    ]
    position_rows = [
        item
        for item in six_digit_contracts
        if item.get("contract_date") == contract_date
        and item.get("trading_session") == "position"
    ]

    if len(after_market_rows) != 1 or len(position_rows) != 1:
        print("錯誤：資料不完整，無法同時取得夜盤與日盤各一筆。")
        raise SystemExit(0)

    after_market = after_market_rows[0]
    position = position_rows[0]

    open_price = _to_int_price(after_market["open"])
    max_price = _to_int_price(max(after_market["max"], position["max"]))
    min_price = _to_int_price(min(after_market["min"], position["min"]))
    close_price = _to_int_price(position["close"])
    volume = int(after_market["volume"] + position["volume"])

    return contract_date, open_price, max_price, min_price, close_price, volume


def main() -> int:
    arg_date = sys.argv[1] if len(sys.argv) > 1 else None
    target_date = _resolve_target_date(arg_date)

    token = _load_finmind_token()
    if not token:
        print("錯誤：找不到 FINMIND_API_TOKEN，請先在 .env 設定。")
        return 0

    data = _request_finmind_data(token, target_date)
    contract_date, open_price, max_price, min_price, close_price, volume = _calculate_summary(data, target_date)

    print(f"商品: {contract_date}")
    print(f"開盤價: {open_price}")
    print(f"最高價: {max_price}")
    print(f"最低價: {min_price}")
    print(f"收盤價: {close_price}")
    print(f"成交量: {volume}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
