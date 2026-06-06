#!/usr/bin/env python3

"""查詢指定期貨商品於日期區間內的每日 OHLCV，整併夜盤／日盤後寫入 data/<id>.tsv"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_DATA_ID = "MTX"
DATA_DIR = Path("data")
HEADER = "日期\t開盤\t最高\t最低\t收盤\t成交量\t是否結算日"
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _load_finmind_token() -> str:
    """優先讀取環境變數，若無則從 .env 載入 FINMIND_API_TOKEN"""
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


def _parse_args(argv: list[str]) -> tuple[str, str, str]:
    """解析命令列參數，回傳（data_id, start_date, end_date）

    參數可不分順序：符合 YYYY-MM-DD 者視為日期（第一個為起日、第二個為訖日），
    其餘字串視為商品代碼。未提供商品時預設 MTX；未提供日期時預設台灣當日，且訖日預設與起日相同
    """
    dates: list[str] = []
    data_id = DEFAULT_DATA_ID

    for arg in argv:
        token = arg.strip()
        if not token:
            continue
        if DATE_PATTERN.match(token):
            try:
                datetime.strptime(token, "%Y-%m-%d")
            except ValueError:
                print(f"錯誤：日期參數格式錯誤（{token}），需為 YYYY-MM-DD")
                raise SystemExit(1)
            dates.append(token)
        else:
            data_id = token

    if not dates:
        today = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d")
        start_date = end_date = today
    elif len(dates) == 1:
        start_date = end_date = dates[0]
    else:
        start_date, end_date = dates[0], dates[1]

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    return data_id.upper(), start_date, end_date


def _request_finmind_range(token: str, data_id: str, start_date: str, end_date: str) -> list[dict]:
    """呼叫 FinMind TaiwanFuturesDaily API 取得指定商品於日期區間的資料；API 失敗則中止，無資料回傳空清單"""
    params = {
        "dataset": "TaiwanFuturesDaily",
        "data_id": data_id,
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
        print("錯誤：FinMind API 請求失敗")
        raise SystemExit(1)

    if payload.get("status") != 200:
        print(f"錯誤：FinMind API 請求失敗（status={payload.get('status')}）")
        raise SystemExit(1)

    return payload.get("data") or []


def _to_int_price(value: int | float) -> int:
    return int(float(value))


def _summarize_date(rows_of_date: list[dict]) -> tuple[int, int, int, int, int] | None:
    """整併某交易日近月合約的夜盤（after_market）與日盤（position）資料

    回傳（開盤, 最高, 最低, 收盤, 成交量）；資料不足以判定時回傳 None
    """
    six_digit = [
        item
        for item in rows_of_date
        if isinstance(item.get("contract_date"), str) and len(item["contract_date"]) == 6
    ]
    if not six_digit:
        return None

    # 近月合約：6 碼到期月份中 ASCII 正序最靠前者
    contract_date = min(item["contract_date"] for item in six_digit)
    nearest = [item for item in six_digit if item.get("contract_date") == contract_date]

    after = next((i for i in nearest if i.get("trading_session") == "after_market"), None)
    position = next((i for i in nearest if i.get("trading_session") == "position"), None)

    if after and position:
        # 完整交易日：開盤取夜盤、最高最低跨盤取極值、收盤優先採非零結算價、成交量加總
        open_price = _to_int_price(after["open"])
        high_price = _to_int_price(max(after["max"], position["max"]))
        low_price = _to_int_price(min(after["min"], position["min"]))
        settle_pos = _to_int_price(position.get("settlement_price", 0))
        settle_am = _to_int_price(after.get("settlement_price", 0))
        if settle_pos != 0:
            close_price = settle_pos
        elif settle_am != 0:
            close_price = settle_am
        else:
            close_price = _to_int_price(position["close"])
        volume = int(after["volume"] + position["volume"])
    elif position:
        # 僅有日盤（夜盤上線前的歷史資料）
        open_price = _to_int_price(position["open"])
        high_price = _to_int_price(position["max"])
        low_price = _to_int_price(position["min"])
        settle_pos = _to_int_price(position.get("settlement_price", 0))
        close_price = settle_pos if settle_pos != 0 else _to_int_price(position["close"])
        volume = int(position["volume"])
    elif after:
        # 僅有夜盤（當日日盤尚未結束）
        open_price = _to_int_price(after["open"])
        high_price = _to_int_price(after["max"])
        low_price = _to_int_price(after["min"])
        settle_am = _to_int_price(after.get("settlement_price", 0))
        close_price = settle_am if settle_am != 0 else _to_int_price(after["close"])
        volume = int(after["volume"])
    else:
        return None

    return open_price, high_price, low_price, close_price, volume


def _is_settlement_day(d: date) -> bool:
    """判斷是否為當月第 3 個星期三（臺指期貨結算日）"""
    # 星期三：weekday() == 2；第 3 個星期三：日期落在第 15 至 21 日
    return d.weekday() == 2 and 15 <= d.day <= 21


def _upsert_rows(path: Path, rows: dict[str, str]) -> tuple[int, int]:
    """將多筆 date 對應的 TSV 列寫入檔案：相同日期則更新，否則新增；回傳（新增筆數, 更新筆數）"""
    existing: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line == HEADER:
                continue
            day = line.split("\t", 1)[0]
            existing[day] = line

    added = updated = 0
    for day, line in rows.items():
        if day in existing:
            if existing[day] != line:
                updated += 1
        else:
            added += 1
        existing[day] = line

    ordered = "\n".join(existing[day] for day in sorted(existing))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{HEADER}\n{ordered}\n", encoding="utf-8")
    return added, updated


def main() -> int:
    data_id, start_date, end_date = _parse_args(sys.argv[1:])

    token = _load_finmind_token()
    if not token:
        print("錯誤：找不到 FINMIND_API_TOKEN，請先在 .env 設定")
        return 1

    data = _request_finmind_range(token, data_id, start_date, end_date)

    # 依交易日分組，僅保留落在區間內的資料
    by_date: dict[str, list[dict]] = {}
    for item in data:
        day = item.get("date")
        if isinstance(day, str) and start_date <= day <= end_date:
            by_date.setdefault(day, []).append(item)

    if not by_date:
        print(f"提示：{data_id} 於 {start_date} ~ {end_date} 區間查無資料（可能為非交易日）")
        return 0

    rows: dict[str, str] = {}
    skipped: list[str] = []
    for day in sorted(by_date):
        summary = _summarize_date(by_date[day])
        if summary is None:
            skipped.append(day)
            continue
        open_price, high_price, low_price, close_price, volume = summary
        settlement = "TRUE" if _is_settlement_day(date.fromisoformat(day)) else "FALSE"
        rows[day] = (
            f"{day}\t{open_price}\t{high_price}\t{low_price}\t{close_price}\t{volume}\t{settlement}"
        )

    if not rows:
        print(f"提示：{data_id} 於 {start_date} ~ {end_date} 區間無可寫入資料")
        return 0

    path = DATA_DIR / f"{data_id.lower()}.tsv"
    added, updated = _upsert_rows(path, rows)

    print(f"商品：{data_id}")
    print(f"區間：{start_date} ~ {end_date}")
    print(f"寫入 {path}：新增 {added} 筆、更新 {updated} 筆（共處理 {len(rows)} 個交易日）")

    preview = sorted(rows)
    if len(preview) > 10:
        print(f"（僅顯示最後 10 筆，共 {len(preview)} 筆）")
        preview = preview[-10:]
    for day in preview:
        print(f"  {rows[day]}")

    if skipped:
        print(f"略過（資料不足）：{', '.join(skipped)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
