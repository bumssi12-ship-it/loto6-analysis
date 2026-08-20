"""
merge_data.py
SOURCE A(미즈호: 회차 · 날짜 · 장소) +
SOURCE B(KYO's: 당첨번호 · 당첨금) → loto6_all.csv 병합

SOURCE B 를 기준으로 LEFT JOIN 하여 전체 회차 (1 회~최신) 를 보존.
"""
import pandas as pd
from pathlib import Path
import logging

logging.basicConfig(
    filename="logs/merge.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

MIZUHO_CSV   = "data/raw/loto6_mizuho.csv"
NUMBERS_CSV  = "data/raw/loto6_numbers.csv"   # .gitignore 대상
OUTPUT_CSV   = "data/raw/loto6_all.csv"

# SOURCE B 컬럼 매핑 (Unicode 문자열로 명시)
# 실제 헤더: ['開催回', '日付', '第 1 数字', '第 2 数字', ...]
COLUMN_MAP = {
    "開催回":     "round",
    "第 1 数字":    "n1", "第 2 数字": "n2", "第 3 数字": "n3",
    "第 4 数字":    "n4", "第 5 数字": "n5", "第 6 数字": "n6",
    "BONUS 数字": "bonus",
    "1 等賞金": "prize1_amount", "1 等口数": "prize1_winners",
    "2 等賞金": "prize2_amount", "2 等口数": "prize2_winners",
    "3 等賞金": "prize3_amount", "3 等口수": "prize3_winners",
    "4 等賞金": "prize4_amount", "4 等口数": "prize4_winners",
    "5 等賞金": "prize5_amount", "5 等口数": "prize5_winners",
}

PRIZE_AMOUNT_COLS = [f"prize{i}_amount" for i in range(1, 6)]
PRIZE_WINNER_COLS = [f"prize{i}_winners" for i in range(1, 6)]


def clean_prize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    당첨금 컬럼 전처리:
    - 쉼표 제거: "200,000,000" → 200000000
    - 결손값("-", 공백) → 0
    - 정수형 변환
    """
    for col in PRIZE_AMOUNT_COLS + PRIZE_WINNER_COLS:
        if col in df.columns:
            df[col] = (
                df[col].astype(str)
                .str.replace(",", "", regex=False)
                .str.replace("-", "0", regex=False)
                .str.strip()
            )
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def merge_sources() -> None:
    """SOURCE A + SOURCE B 를 round 기준으로 병합해 loto6_all.csv 저장"""
    df_a = pd.read_csv(MIZUHO_CSV, encoding="utf-8")
    # SOURCE B 는 Shift-JIS 인코딩 (cp932 대신 shift_jis 사용)
    df_b = pd.read_csv(NUMBERS_CSV, encoding="shift_jis")
    
    logging.info(f"SOURCE B 원본 컬럼: {df_b.columns.tolist()[:5]}...")
    
    # 컬럼 매핑 적용
    df_b = df_b.rename(columns=COLUMN_MAP)
    
    logging.info(f"매핑 후 컬럼: {df_b.columns.tolist()[:5]}...")
    
    # 당첨금 컬럼 정제
    df_b = clean_prize_columns(df_b)
    
    # SOURCE B 를 기준으로 LEFT JOIN (전체 회차 보존)
    df_merged = pd.merge(df_b, df_a, on="round", how="left")
    df_merged["draw_date"] = pd.to_datetime(df_merged["draw_date"], errors="coerce")
    df_merged.sort_values("round", ascending=False, inplace=True)

    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)
    df_merged.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    logging.info(f"병합 완료: {OUTPUT_CSV} ({len(df_merged)}건)")
    logging.info(f"최종 컬럼: {df_merged.columns.tolist()[:8]}...")


if __name__ == "__main__":
    merge_sources()
