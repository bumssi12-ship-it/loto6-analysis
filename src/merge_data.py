"""
merge_data.py
SOURCE A（みずほ）+ SOURCE B（KYO's）→ loto6_all.csv に統合
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    filename="logs/merge.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)

MIZUHO_CSV = "data/raw/loto6_mizuho.csv"
NUMBERS_CSV = "data/raw/loto6_numbers.csv"
OUTPUT_CSV = "data/raw/loto6_all.csv"

COLUMN_MAP = {
    "回号": "round",
    "第1数字": "n1", "第2数字": "n2", "第3数字": "n3",
    "第4数字": "n4", "第5数字": "n5", "第6数字": "n6",
    "ボーナス数字": "bonus",
    "1等当せん金額": "prize1_amount", "1等当せん口数": "prize1_winners",
    "2等当せん金額": "prize2_amount", "2等当せん口数": "prize2_winners",
    "3等当せん金額": "prize3_amount", "3等当せん口数": "prize3_winners",
    "4等当せん金額": "prize4_amount", "4等当せん口数": "prize4_winners",
    "5等当せん金額": "prize5_amount", "5等当せん口数": "prize5_winners",
    "6等当せん金額": "prize6_amount", "6等当せん口数": "prize6_winners",
}

PRIZE_AMOUNT_COLS = [f"prize{i}_amount" for i in range(1, 7)]
PRIZE_WINNER_COLS = [f"prize{i}_winners" for i in range(1, 7)]


def clean_prize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    当せん金・口数カラムを前処理する（カンマ除去・欠損値0埋め・整数変換）。

    Args:
        df: SOURCE B の生データ
    Returns:
        前処理済みのDataFrame
    """
    for col in PRIZE_AMOUNT_COLS + PRIZE_WINNER_COLS:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("-", "0", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def merge_sources(
    mizuho_path: str = MIZUHO_CSV,
    numbers_path: str = NUMBERS_CSV,
    output_path: str = OUTPUT_CSV,
) -> pd.DataFrame:
    """
    SOURCE A + SOURCE B を round 基準で統合し loto6_all.csv に保存する。

    Args:
        mizuho_path: SOURCE A（みずほ）CSVパス
        numbers_path: SOURCE B（KYO's）CSVパス
        output_path: 統合結果の保存先パス
    Returns:
        統合済みDataFrame
    """
    if not Path(numbers_path).exists():
        raise FileNotFoundError(
            f"{numbers_path} が見つかりません。"
            " KYO's LOTO6 (https://loto6.thekyo.jp/download/index) から"
            " 手動ダウンロードして配置してください（再配布・コミット禁止）。"
        )

    df_a = pd.read_csv(mizuho_path, encoding="utf-8")
    df_b = pd.read_csv(numbers_path, encoding="utf-8")
    df_b = df_b.rename(columns=COLUMN_MAP)
    df_b = clean_prize_columns(df_b)

    df_merged = pd.merge(df_a, df_b, on="round", how="inner")
    df_merged["draw_date"] = pd.to_datetime(df_merged["draw_date"], errors="coerce")
    df_merged = df_merged.sort_values("round", ascending=False).reset_index(drop=True)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df_merged.to_csv(output_path, index=False, encoding="utf-8")
    logging.info("統合完了: %s (%d件)", output_path, len(df_merged))

    return df_merged


if __name__ == "__main__":
    merge_sources()
