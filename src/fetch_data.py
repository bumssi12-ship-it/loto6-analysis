"""
fetch_data.py
みずほ銀行公式CSV収集モジュール（実際の構造に基づく）
構造: A52行（スキップ）+ データ行、2行1セット、UTF-8, CRLF

[注記] みずほ銀行サーバーのWAFがデータスタ/HTTPクリエントを403 Forbiddenで
ブロッキすることが確認されている（ローカルPCとGitHub Actionsの両方で発生）。
その場合はブラウザで手動ダウンロードし、--local でローカルファイルを渡すこと。
"""
from __future__ import annotations

import argparse
import re
import logging
from datetime import datetime
from pathlib import Path

import requests
import pandas as pd

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    filename="logs/fetch.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)

MIZUHO_URL = (
    "https://www.mizuhobank.co.jp"
    "/retail/takarakuji/loto/loto6/csv/loto6.csv"
)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/csv,text/plain,*/*",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.mizuhobank.co.jp/retail/takarakuji/loto/loto6/index.html",
}

ERA_BASE = {"令和": 2018, "平成": 1988, "昭和": 1925}
ERA_PATTERN = re.compile(r"(令和|平成|昭和)(\d+)年(\d+)月(\d+)日")
ROUND_PATTERN = re.compile(r"第(\d+)回")


def wareki_to_seireki(wareki: str) -> str:
    """
    日本の和暦日付を西暦 YYYY-MM-DD に変換する。

    Args:
        wareki: 和暦表記の文字列（例: "令和7年7月31日"）
    Returns:
        西暦文字列（例: "2025-07-31"）。変換失敗時は元の文字列を返す。
    """
    m = ERA_PATTERN.match(wareki.strip())
    if not m:
        logging.warning("元号変換失敗: %s", wareki)
        return wareki
    era, y, mo, d = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
    year = ERA_BASE[era] + y
    return f"{year:04d}-{mo:02d}-{d:02d}"


def parse_mizuho_csv(text: str) -> list[dict]:
    """
    みずほ公式CSV原文をパースしてレコードのリストを返す。

    Args:
        text: CSV原文全体の文字列
    Returns:
        [{"round": int, "draw_date": str, "venue": str}, ...]
    """
    lines = text.strip().splitlines()
    records: list[dict] = []

    for i in range(0, len(lines) - 1, 2):
        code_line = lines[i].strip()
        data_line = lines[i + 1].strip()

        if code_line != "A52":
            logging.warning("予期しないコード行: %s (行 %d)", code_line, i + 1)
            continue

        parts = [p.strip() for p in data_line.split(",")]
        if len(parts) < 3:
            logging.warning("フィールド不足: %s", data_line)
            continue

        round_match = ROUND_PATTERN.search(parts[0])
        if not round_match:
            logging.warning("回号パース失敗: %s", parts)
            continue
        round_num = int(round_match.group(1))

        draw_date = wareki_to_seireki(parts[2])
        venue = parts[3] if len(parts) > 3 else ""

        records.append({
            "round": round_num,
            "draw_date": draw_date,
            "venue": venue,
        })

    return records


def _read_local_text(path: str) -> str:
    """
    ブラウザで手動保存したCSVファイルをUTF-8として読み込む。
    UTF-8で失敗した場合はShift-JIS（cp932）でリトリイする。

    Args:
        path: ローカルCSVファイルパス
    Returns:
        ファイル内容の文字列
    """
    p = Path(path)
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        logging.warning("UTF-8読み込み失敗、Shift-JISで再試行: %s", path)
        return p.read_text(encoding="cp932")


def fetch_and_save(
    url: str = MIZUHO_URL,
    output: str = "data/raw/loto6_mizuho.csv",
    local_path: str | None = None,
) -> None:
    """
    みずほ公式CSVを取得（またはローカルファイルから読込）し、正規化して保存する。

    Args:
        url: 取得対象URL（local_pathが指定されていれば無視される）
        output: 保存先パス
        local_path: 指定された場合、リブック取得の代わりにこのローカル
            ファイルをパースする（403 Forbidden等でHTTP取得できない場合の
            回避策。ブラウザで手動ダウンロードしたCSVを渡すこと）
    """
    try:
        if local_path:
            logging.info("ローカルファイルから読込: %s", local_path)
            text = _read_local_text(local_path)
        else:
            logging.info("収集開始: %s", url)
            session = requests.Session()
            session.headers.update(HEADERS)
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            text = resp.text

        records = parse_mizuho_csv(text)

        if not records:
            raise ValueError("パース結果が0件です。CSV構造が変更された可能性があります。")

        Path(output).parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(records).sort_values("round", ascending=False)
        df.to_csv(output, index=False, encoding="utf-8")

        Path("data").mkdir(parents=True, exist_ok=True)
        Path("data/last_updated.txt").write_text(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            encoding="utf-8",
        )
        logging.info("保存完了: %s (%d件)", output, len(df))

    except requests.RequestException as e:
        logging.error("HTTPエラー: %s", e)
        raise
    except Exception as e:
        logging.error("予期しないエラー: %s", e)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="みずほ公式CSV収集")
    parser.add_argument(
        "--local",
        dest="local_path",
        default=None,
        help=(
            "403 Forbidden等でHTTP取得できない場合、ブラウザで手動保存した"
            "CSVファイルのパスを指定する"
        ),
    )
    args = parser.parse_args()
    fetch_and_save(local_path=args.local_path)
