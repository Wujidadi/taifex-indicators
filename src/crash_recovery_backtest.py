#!/usr/bin/env python3

"""台指期（MTX／TX）歷史急殺後之報酬與回補時程回測

定義「急殺事件」為單日收盤對收盤跌幅 <= 門檻（預設 -5%），並對相鄰急殺日去叢集
（前 10 個交易日內無其他急殺日者，視為一次獨立事件之起點）。對每次事件計算：

  - 事件前一日收盤（pre）作為「崩跌前水準」基準（對應本次的約 45,000）
  - 事件日後 1／5／10／20／60 日之收盤對收盤報酬
  - 事件日後再下探的最大續跌幅（相對事件日收盤）
  - 自事件日起，收盤重新站回 pre 所需之交易日數（回補時程）

用法：python3 src/crash_recovery_backtest.py [商品=mtx] [門檻%=-5]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HORIZONS = [1, 5, 10, 20, 60]
RECOVER_BUCKETS = [5, 10, 20, 60, 120, 250]
CLUSTER_GAP = 10          # 去叢集：前 N 個交易日內無急殺日才算新事件
MAX_LOOKAHEAD = 504       # 回補搜尋上限（約兩年交易日）


def load_closes(data_id: str) -> pd.DataFrame:
    path = Path("data") / f"{data_id}.tsv"
    df = pd.read_csv(path, sep="\t", dtype={"日期": str})
    df = df.rename(columns={"日期": "date", "收盤": "close", "最低": "low"})
    # 排除尚未完成之夜盤列（僅有夜盤、無日盤的當前進行中交易日）
    df = df[df["date"] <= "2026-06-05"].reset_index(drop=True)
    df["ret"] = df["close"].pct_change()
    return df


def find_events(df: pd.DataFrame, thr: float) -> list[int]:
    """回傳去叢集後之事件列索引（事件日 = 急殺日）"""
    shock_idx = df.index[df["ret"] <= thr].tolist()
    events: list[int] = []
    last = -10 ** 9
    for i in shock_idx:
        if i - last > CLUSTER_GAP:
            events.append(i)
        last = i
    return events


def analyze_event(df: pd.DataFrame, i: int) -> dict:
    close = df["close"].to_numpy()
    low = df["low"].to_numpy()
    n = len(close)
    pre = close[i - 1]                       # 崩跌前一日收盤（基準）
    d_close = close[i]

    fwd = {}
    for h in HORIZONS:
        fwd[h] = (close[i + h] / d_close - 1.0) if i + h < n else np.nan

    # 事件日後（含事件日起算）之最低收盤與最低點，量化續跌
    end = min(n, i + MAX_LOOKAHEAD + 1)
    seg_close = close[i:end]
    seg_low = low[i:end]
    min_close_dd = seg_close.min() / d_close - 1.0
    min_low_dd = seg_low.min() / d_close - 1.0

    # 回補：自事件日後，收盤首次 >= pre 所需交易日數
    recover_days = np.nan
    for k in range(1, end - i):
        if close[i + k] >= pre:
            recover_days = k
            break

    return {
        "date": df["date"].iloc[i],
        "ret": df["ret"].iloc[i],
        "pre": pre,
        "close": d_close,
        "fwd": fwd,
        "min_close_dd": min_close_dd,
        "min_low_dd": min_low_dd,
        "recover_days": recover_days,
    }


def pct(x: float) -> str:
    return "nan" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x * 100:+6.2f}%"


def summarize(events: list[dict], thr: float, data_id: str) -> None:
    n = len(events)
    print(f"\n{'=' * 78}")
    print(f"商品 {data_id.upper()}｜門檻 單日收盤跌幅 <= {thr * 100:.1f}%｜去叢集事件數 = {n}")
    print(f"{'=' * 78}")

    # 各事件明細
    print(f"\n{'事件日':<12}{'當日':>8}{'+1':>8}{'+5':>8}{'+10':>8}{'+20':>8}{'+60':>8}{'續跌低':>9}{'回補日':>7}")
    for e in events:
        rec = e["recover_days"]
        rec_s = "未補" if (rec is None or (isinstance(rec, float) and np.isnan(rec))) else f"{int(rec)}"
        print(
            f"{e['date']:<12}{pct(e['ret']):>8}{pct(e['fwd'][1]):>8}{pct(e['fwd'][5]):>8}"
            f"{pct(e['fwd'][10]):>8}{pct(e['fwd'][20]):>8}{pct(e['fwd'][60]):>8}"
            f"{pct(e['min_low_dd']):>9}{rec_s:>7}"
        )

    # 前向報酬分佈
    print("\n-- 事件日後報酬分佈（收盤對收盤；中位數 / 平均 / 為正比例）--")
    for h in HORIZONS:
        vals = np.array([e["fwd"][h] for e in events if not np.isnan(e["fwd"][h])])
        if len(vals) == 0:
            continue
        print(
            f"  +{h:>3} 日：中位 {pct(np.median(vals))}  平均 {pct(np.mean(vals))}  "
            f"為正 {(vals > 0).mean() * 100:4.0f}%  最佳 {pct(vals.max())}  最差 {pct(vals.min())}"
        )

    # 續跌幅
    low_dd = np.array([e["min_low_dd"] for e in events])
    close_dd = np.array([e["min_close_dd"] for e in events])
    print("\n-- 事件日後再下探（相對事件日收盤）--")
    print(f"  最低收盤續跌：中位 {pct(np.median(close_dd))}  最深 {pct(close_dd.min())}")
    print(f"  最低點續跌  ：中位 {pct(np.median(low_dd))}  最深 {pct(low_dd.min())}")

    # 回補時程
    recs = [e["recover_days"] for e in events]
    finite = np.array([r for r in recs if r is not None and not (isinstance(r, float) and np.isnan(r))])
    print("\n-- 回補崩跌前水準（收盤站回 pre）所需交易日 --")
    for b in RECOVER_BUCKETS:
        share = np.mean([(r is not None and not np.isnan(r) and r <= b) for r in recs]) * 100
        print(f"  {b:>4} 日內回補比例：{share:4.0f}%")
    if len(finite) > 0:
        print(
            f"  已回補事件：中位 {int(np.median(finite))} 日  下四分位 {int(np.percentile(finite, 25))} 日  "
            f"上四分位 {int(np.percentile(finite, 75))} 日  最快 {int(finite.min())} 日  最慢 {int(finite.max())} 日"
        )
    n_unrec = sum(1 for r in recs if r is None or (isinstance(r, float) and np.isnan(r)))
    print(f"  {MAX_LOOKAHEAD} 交易日內仍未回補：{n_unrec} 次")


def main() -> int:
    data_id = (sys.argv[1] if len(sys.argv) > 1 else "mtx").lower()
    thr_arg = float(sys.argv[2]) / 100 if len(sys.argv) > 2 else None

    df = load_closes(data_id)
    print(f"資料：data/{data_id}.tsv｜{df['date'].iloc[0]} ~ {df['date'].iloc[-1]}｜{len(df)} 個交易日")
    cur_ret = 42182 / 45226 - 1 if data_id == "mtx" else 42220 / 45226 - 1
    print(f"本次事件（6/5 收 45226 → 6/8 夜盤收 ~42200）約當單日 {pct(cur_ret)}（基準/崩前水準 ≈ 45,000）")

    thresholds = [thr_arg] if thr_arg is not None else [-0.04, -0.05, -0.06, -0.07]
    for thr in thresholds:
        idxs = find_events(df, thr)
        events = [analyze_event(df, i) for i in idxs]
        summarize(events, thr, data_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
