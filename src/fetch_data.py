"""
fetch_data.py
SOURCE A: みずほ銀行 ロト6 当選番号データ (https://www.mizuhobank.co.jp/lototaka/loto6/index.html)

スクレイピング禁止のため、手動ダウンロードを推奨。
"""
import requests
import pandas as pd
from pathlib import Path
import logging
import re
from datetime import datetime

logging.basicConfig(
    filename="logs/fetch.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

OUTPUT_CSV = "data/raw/loto6_mizuho.csv"

# みずほ銀行 URL (スクレイピング禁止のため参考のみ)
# URL = "https://www.mizuhobank.co.jp/lototaka/loto6/index.html"


def fetch_mizuho_data() -> pd.DataFrame:
    """
    みずほ銀行からロト6データを取得 (現在は手動ダウンロード推奨)
    
    Returns:
        DataFrame: 回号、抽選日、会場
    """
    # 手動ダウンロード用: 既存の CSV を使用
    if Path(OUTPUT_CSV).exists():
        logging.info(f"既存の {OUTPUT_CSV} を使用します")
        return pd.read_csv(OUTPUT_CSV, encoding="utf-8")
    
    # 新規取得は WAF により 403 になる可能性が高い
    logging.warning("みずほ銀行の自動取得は WAF により失敗する可能性があります")
    raise RuntimeError("手動ダウンロードが必要です: https://loto6.thekyo.jp/download/index")


def main() -> None:
    """SOURCE A データを保存"""
    try:
        df = fetch_mizuho_data()
    except RuntimeError as e:
        logging.error(str(e))
        # 既存データがあれば使用
        if Path(OUTPUT_CSV).exists():
            logging.info("既存データで継続します")
            return
        raise
    
    Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    logging.info(f"保存: {OUTPUT_CSV} ({len(df)}件)")


if __name__ == "__main__":
    main()
