#!/usr/bin/env python3

"""取得 MTX 當日夜盤/日盤整併後的價量摘要。"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
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


def _request_finmind_range(token: str, start_date: str, end_date: str) -> list[dict]:
    """呼叫 FinMind API 取得 MTX 指定日期區間的資料。API 錯誤則 SystemExit，無資料返回空清單。"""
    params = {
        "dataset": "TaiwanFuturesDaily",
        "data_id": "MTX",
        "start_date": start_date,
        "end_date": end_date,
    }
    query = urllib.parse.urlencode(params)
    url = f"https://api.finmindtrade.com/api/v4/data?{query}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        print("錯誤：FinMind API 請求失敗。")
        raise SystemExit(0)

    if payload.get("status") != 200:
        print("錯誤：FinMind API 請求失敗。")
        raise SystemExit(0)

    return payload.get("data") or []


def _get_nearest_contract_date(data: list[dict], day: str) -> str | None:
    """取得指定日期最小（ASCII 正序最靠前）的 6 碼 contract_date。"""
    contracts = [
        item["contract_date"]
        for item in data
        if item.get("date") == day
        and isinstance(item.get("contract_date"), str)
        and len(item["contract_date"]) == 6
    ]
    return min(contracts) if contracts else None


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

    # 收盤價：優先使用非零的 settlement_price（日結算價），position 優先於 after_market
    settlement_pos = _to_int_price(position.get("settlement_price", 0))
    settlement_am  = _to_int_price(after_market.get("settlement_price", 0))
    if settlement_pos != 0:
        close_price = settlement_pos
    elif settlement_am != 0:
        close_price = settlement_am
    else:
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

    target_dt = datetime.strptime(target_date, "%Y-%m-%d")
    is_thursday = target_dt.weekday() == 3  # 0=Monday … 3=Thursday

    prev_date: str | None = None
    prev_was_settlement: bool | None = None
    all_data: list[dict] = []

    if is_thursday:
        # 指定日期為星期四：嘗試將 start_date 往前延伸至最近的交易日，
        # 使當日與前一交易日的資料可在同一次 API 請求中取得
        prev_dt = target_dt - timedelta(days=1)
        for _ in range(14):
            candidate = prev_dt.strftime("%Y-%m-%d")
            fetched = _request_finmind_range(token, candidate, target_date)
            if any(item.get("date") == candidate for item in fetched):
                prev_date = candidate
                all_data = fetched
                break
            prev_dt -= timedelta(days=1)

        if not all_data:
            # 往前 14 天均無資料，僅抓 target_date
            all_data = _request_finmind_range(token, target_date, target_date)

        if not any(item.get("date") == target_date for item in all_data):
            print("錯誤：指定日期查無 MTX 資料。")
            return 0

        if prev_date:
            target_contract = _get_nearest_contract_date(all_data, target_date)
            prev_contract   = _get_nearest_contract_date(all_data, prev_date)
            if target_contract and prev_contract:
                prev_was_settlement = target_contract != prev_contract
    else:
        all_data = _request_finmind_range(token, target_date, target_date)
        if not all_data:
            print("錯誤：指定日期查無 MTX 資料。")
            return 0

    contract_date, open_price, max_price, min_price, close_price, volume = _calculate_summary(all_data, target_date)

    print(f"商品: {contract_date}")
    print(f"開盤價: {open_price}")
    print(f"最高價: {max_price}")
    print(f"最低價: {min_price}")
    print(f"收盤價: {close_price}")
    print(f"成交量: {volume}")

    if prev_date is not None:
        print(f"前日: {prev_date}")
    if prev_was_settlement is not None:
        print(f"前日結算日: {'TRUE' if prev_was_settlement else 'FALSE'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
