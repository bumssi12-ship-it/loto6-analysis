"""
app.py — ロト6統計分析 Streamlitダッシュボード
GA4タグ + Measurement Protocol 連携
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

GA4_ID: str = os.getenv("GA4_MEASUREMENT_ID", "")
GA4_SECRET: str = os.getenv("GA4_API_SECRET", "")

NUMBER_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]


def inject_ga4_tag() -> None:
    """GA4グローバルタグをStreamlitに挿入する（GA4_IDが未設定なら何もしない）。"""
    if not GA4_ID:
        return
    components.html(f"""
    <script async
      src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}">
    </script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA4_ID}');
    </script>
    """, height=0)


def send_ga4_event(event_name: str, params: dict | None = None) -> None:
    """
    GA4 Measurement Protocolでカスタムイベントを送信する。

    Args:
        event_name: イベント名
        params: イベントパラメータ
    """
    if params is None:
        params = {}
    try:
        from ga4mp import GtagMP
        if not GA4_ID or not GA4_SECRET:
            return
        ga = GtagMP(
            measurement_id=GA4_ID,
            api_secret=GA4_SECRET,
            client_id="loto6-streamlit-app",
        )
        ga.send([{"name": event_name, "params": params}])
    except Exception:
        pass


def compute_hot_cold_live(df: pd.DataFrame, recent_n: int) -> pd.DataFrame:
    """
    サイドバーで指定した直近N回に基づき、ホット/コールド番号をライブ集計する。

    Args:
        df: round昇順の全データ
        recent_n: 直近何回を対象にするか
    Returns:
        number, count_recent, status を持つDataFrame
    """
    recent = df.sort_values("round").tail(recent_n)
    counts = (
        pd.Series(recent[NUMBER_COLS].values.flatten())
        .value_counts()
        .reindex(range(1, 44), fill_value=0)
    )
    return pd.DataFrame({
        "number": counts.index,
        "count_recent": counts.values,
        "status": counts.apply(
            lambda x: "hot" if x >= 3 else ("cold" if x == 0 else "normal")
        ),
    })


st.set_page_config(page_title="ロト6統計分析", page_icon="🎯", layout="wide")
inject_ga4_tag()
send_ga4_event("page_view", {"page_title": "loto6_dashboard"})

st.error(
    "⚠️ 本分析は統計的傾向の可視化のみを目的とし、"
    "当選を保証するものではありません。"
    " / 이 분석은 통계적 경향 시각화 목적으로만 제공되며, "
    "당첨을 보장하지 않습니다。"
)

updated_path = Path("data/last_updated.txt")
if updated_path.exists():
    st.caption(f"最終更新: {updated_path.read_text(encoding='utf-8').strip()}")

df_all = pd.read_csv("data/raw/loto6_all.csv", encoding="utf-8", comment="#")

st.sidebar.title("🎛️ フィルター設定")
min_r, max_r = int(df_all["round"].min()), int(df_all["round"].max())
r_range = st.sidebar.slider("回号範囲", min_r, max_r, (min_r, max_r), step=1)
recent_n = st.sidebar.number_input(
    "ホット/コールド判定 直近N回", min_value=10, max_value=100, value=30, step=5
)
lang = st.sidebar.selectbox("言語 / 언어", ["日本語", "한국어"])

round_from, round_to = r_range[0], r_range[1]
mask = (df_all["round"] >= round_from) & (df_all["round"] <= round_to)
df_filtered = df_all[mask]

send_ga4_event("filter_applied", {"round_from": round_from, "round_to": round_to})

hot_cold_live = compute_hot_cold_live(df_filtered, int(recent_n))

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 番号頻度", "🔗 組合分析", "💰 当せん金推移", "📋 データテーブル"]
)


def load_chart_html(name: str) -> str:
    path = Path(f"charts/{name}.html")
    return path.read_text(encoding="utf-8") if path.exists() else ""


with tab1:
    st.subheader("番号別出現頻度")
    html = load_chart_html("freq_bar")
    if html:
        components.html(html, height=500, scrolling=True)
        send_ga4_event("chart_viewed", {"chart_type": "freq_bar"})
    else:
        st.info("charts/freq_bar.html が見つかりません。src/visualize.py を実行してください。")

    st.subheader(f"直近{int(recent_n)}回 ホット/コールド番号（ライブ集計）")
    st.dataframe(hot_cold_live, use_container_width=True)

with tab2:
    st.subheader("同時出現ペア頻度 (ヒートマップ)")
    html = load_chart_html("pair_heatmap")
    if html:
        components.html(html, height=600, scrolling=True)
        send_ga4_event("chart_viewed", {"chart_type": "pair_heatmap"})
    else:
        st.info("charts/pair_heatmap.html が見つかりません。src/visualize.py を実行してください。")

with tab3:
    st.subheader("1等当せん金額推移")
    html = load_chart_html("jackpot_trend")
    if html:
        components.html(html, height=500, scrolling=True)
        send_ga4_event("chart_viewed", {"chart_type": "jackpot_trend"})
    else:
        st.info("charts/jackpot_trend.html が見つかりません。src/visualize.py を実行してください。")

with tab4:
    st.subheader("抽せんデータ一覧")
    st.dataframe(df_filtered, use_container_width=True)
