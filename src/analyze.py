"""
analyze.py — 7種統計分析モジュール
入力: data/raw/loto6_all.csv
出力: data/analysis/*.csv （各ファイル先頭行に免責コメントを含む）
"""
from __future__ import annotations

import itertools
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO)

DISCLAIMER = (
    "# 本分析は統計的傾向の可視化のみ。"
    "当選を保証するものではありません。\n"
)
NUMBER_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]
OUT_DIR = Path("data/analysis")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def save_with_disclaimer(df: pd.DataFrame, path: str | Path, index: bool = False) -> None:
    """
    CSV保存時に先頭行へ免責コメントを挿入する。

    Args:
        df: 保存対象のDataFrame
        path: 保存先パス
        index: True の場合、DataFrameのインデックスも保存する
    """
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(DISCLAIMER)
        df.to_csv(f, index=index)
    logging.info("保存: %s", path)


def load_data(path: str = "data/raw/loto6_all.csv") -> pd.DataFrame:
    """分析用データを読み込み、基本前処理を行う。"""
    df = pd.read_csv(path, encoding="utf-8", comment="#")
    df["draw_date"] = pd.to_datetime(df["draw_date"], errors="coerce")
    return df.sort_values("round").reset_index(drop=True)


def analyze_freq(df: pd.DataFrame) -> None:
    """番号別出現頻度分析（1〜43）"""
    all_nums = df[NUMBER_COLS].values.flatten()
    counts = pd.Series(all_nums).value_counts().reindex(range(1, 44), fill_value=0)
    total = counts.sum()
    result = pd.DataFrame({
        "number": counts.index,
        "count": counts.values,
        "rate_pct": (counts.values / total * 100).round(2) if total else 0.0,
    })
    save_with_disclaimer(result, OUT_DIR / "freq_all.csv")


def analyze_hot_cold(df: pd.DataFrame, recent_n: int = 30) -> None:
    """直近N回に基づくホット/コールド番号分析"""
    recent = df.tail(recent_n)
    counts = (
        pd.Series(recent[NUMBER_COLS].values.flatten())
        .value_counts()
        .reindex(range(1, 44), fill_value=0)
    )
    result = pd.DataFrame({
        "number": counts.index,
        "count_recent": counts.values,
        "status": counts.apply(
            lambda x: "hot" if x >= 3 else ("cold" if x == 0 else "normal")
        ),
    })
    save_with_disclaimer(result, OUT_DIR / "hot_cold.csv")


def analyze_odd_even(df: pd.DataFrame) -> None:
    """回号別 奇偶・高低比率分析"""
    nums = df[NUMBER_COLS]
    result = df[["round", "draw_date"]].copy()
    result["odd_count"] = (nums % 2 == 1).sum(axis=1)
    result["even_count"] = (nums % 2 == 0).sum(axis=1)
    result["low_count"] = (nums <= 21).sum(axis=1)
    result["high_count"] = (nums >= 22).sum(axis=1)
    save_with_disclaimer(result, OUT_DIR / "odd_even_high_low.csv")


def analyze_pairs(df: pd.DataFrame) -> None:
    """同時出現ペア頻度行列（43×43、対角線=0）"""
    matrix = np.zeros((43, 43), dtype=int)
    for _, row in df[NUMBER_COLS].iterrows():
        for a, b in itertools.combinations(row.tolist(), 2):
            matrix[int(a) - 1][int(b) - 1] += 1
            matrix[int(b) - 1][int(a) - 1] += 1
    result = pd.DataFrame(matrix, index=range(1, 44), columns=range(1, 44))
    save_with_disclaimer(result, OUT_DIR / "pair_matrix.csv", index=True)


def analyze_sum(df: pd.DataFrame) -> None:
    """回号別 番号合計分布分析"""
    result = df[["round", "draw_date"]].copy()
    result["sum"] = df[NUMBER_COLS].sum(axis=1)
    result["bin"] = pd.cut(result["sum"], bins=range(20, 261, 20), right=False).astype(str)
    save_with_disclaimer(result, OUT_DIR / "sum_distribution.csv")


def analyze_jackpot(df: pd.DataFrame) -> None:
    """1等当せん金時系列 + 20回移動平均"""
    result = df[["round", "draw_date", "prize1_amount"]].copy()
    result["ma20"] = result["prize1_amount"].rolling(20).mean().round(0)
    save_with_disclaimer(result, OUT_DIR / "jackpot_trend.csv")


def analyze_bonus(df: pd.DataFrame) -> None:
    """ボーナス番号出現頻度"""
    counts = df["bonus"].value_counts().reindex(range(1, 44), fill_value=0)
    result = pd.DataFrame({"number": counts.index, "count": counts.values})
    save_with_disclaimer(result, OUT_DIR / "bonus_freq.csv")


if __name__ == "__main__":
    df = load_data()
    analyze_freq(df)
    analyze_hot_cold(df)
    analyze_odd_even(df)
    analyze_pairs(df)
    analyze_sum(df)
    analyze_jackpot(df)
    analyze_bonus(df)
    logging.info("全分析完了")
