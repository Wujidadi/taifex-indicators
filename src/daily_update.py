#!/usr/bin/env python3

"""每日排程入口：將 TX／MTX／TMF 的 data/<id>.tsv 補抓至台灣當日，並重新產生 reports/<id>.tsv

起日取 data/<id>.tsv 最後一列的日期，因此排程漏跑數日後仍會一次補齊
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DATA_IDS = ("TX", "MTX", "TMF")
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _last_date(path: Path) -> str | None:
    """回傳 TSV 最後一列的日期；檔案不存在或無資料列時回傳 None"""
    if not path.exists():
        return None
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return None
    day = lines[-1].split("\t", 1)[0]
    return day if DATE_PATTERN.match(day) else None


def _run(*args: str) -> bool:
    return subprocess.run([sys.executable, *args], check=False).returncode == 0


def main() -> int:
    os.chdir(PROJECT_DIR)
    now = datetime.now(ZoneInfo("Asia/Taipei"))
    today = now.strftime("%Y-%m-%d")
    print(f"===== {now.isoformat(timespec='seconds')} =====", flush=True)

    failed = False
    for data_id in DATA_IDS:
        start_date = _last_date(Path("data") / f"{data_id.lower()}.tsv") or today
        ok = _run("src/finmind_futures_daily.py", data_id, start_date, today) and _run(
            "src/analyze_futures.py", data_id
        )
        failed = failed or not ok

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
