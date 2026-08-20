"""
app.py — ロト 6 統計分析 Streamlit 대시보드
GA4 태그 + Measurement Protocol 포함 + 추천번호 기능
"""
import os
import time
import uuid
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── GA4 설정 ─────────────────────────────────────────────
GA4_ID = os.getenv("GA4_MEASUREMENT_ID", "")
GA4_SECRET = os.getenv("GA4_API_SECRET", "")


def get_client_id() -> str:
    """세션별 고유 client_id 를 생성/유지 (활성 사용자 집계용)."""
    if "ga4_client_id" not in st.session_state:
        st.session_state["ga4_client_id"] = str(uuid.uuid4())
    return st.session_state["ga4_client_id"]


def get_session_id() -> str:
    """세션 시작 시각 기반 session_id 를 생성/유지 (세션 귀속용)."""
    if "ga4_session_id" not in st.session_state:
        st.session_state["ga4_session_id"] = str(int(time.time()))
    return st.session_state["ga4_session_id"]


def inject_ga4_tag() -> None:
    """GA4 글로벌 태그를 Streamlit 에 삽입 (클라이언트 측 gtag.js)."""
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
    GA4 Measurement Protocol 로 서버 측 커스텀 이벤트 전송.
    pip install ga4mp
    """
    if params is None:
        params = {}
    try:
        from ga4mp import GtagMP
        if not GA4_ID or not GA4_SECRET:
            return
        client_id = get_client_id()
        session_id = get_session_id()

        event_params = {
            **params,
            "engagement_time_msec": "1",
            "session_id": session_id,
        }

        ga = GtagMP(
            measurement_id=GA4_ID,
            api_secret=GA4_SECRET,
            client_id=client_id,
        )
        ga.send([{"name": event_name, "params": event_params}])
    except Exception:
        pass


# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="ロト 6 統計分析",
    page_icon="🎯",
    layout="wide"
)
inject_ga4_tag()
send_ga4_event("page_view", {"page_title": "loto6_dashboard"})

# ── 면책 배너 (항상 최상단 표시) ─────────────────────────
st.error(
    "⚠️ 本分析は統計的傾向の可視化のみを目的とし、"
    "当選を保証するものではありません。"
    " / 이 분석은 통계적 경향 시각화 목적으로만 제공되며, "
    "당첨을 보장하지 않습니다."
)

# ── 추천번호 면책 배너 (추천 탭 전용) ────────────────────
st.warning(
    "🎲 番号推薦は統計的パターンに基づく参考値です。"
    "当選を約束するものではありません。"
    " / 추천번호는 통계적 패턴 기반 참고용이며, 당첨을 보장하지 않습니다."
)

# ── 갱신일 표시 ──────────────────────────────────────────
updated_path = Path("data/last_updated.txt")
if updated_path.exists():
    st.caption(f"最終更新：{updated_path.read_text(encoding='utf-8').strip()}")

# ── 데이터 로드 ──────────────────────────────────────────
df_all = pd.read_csv("data/raw/loto6_all.csv", encoding="utf-8", comment="#")

# ── 사이드바 ─────────────────────────────────────────────
st.sidebar.title("🎛️ フィルター設定")
min_r, max_r = int(df_all["round"].min()), int(df_all["round"].max())
r_range = st.sidebar.slider(
    "回号範囲", min_r, max_r, (min_r, max_r), step=1
)
recent_n = st.sidebar.number_input(
    "ホット/コールド判定 直近 N 回", min_value=10, max_value=100,
    value=30, step=5
)
lang = st.sidebar.selectbox("言語 / 언어", ["日本語", "한국어"])

# 추천 설정
st.sidebar.title("🎲 推薦設定")
rec_mode = st.sidebar.selectbox(
    "推薦モード",
    ["balanced", "hot", "cold", "random"],
    format_func=lambda x: {
        "balanced": "균형 (핫 + 노멀)",
        "hot": "핫 넘버 위주",
        "cold": "콜드 넘버 포함",
        "random": "완전 랜덤"
    }.get(x, x)
)
n_rec = st.sidebar.slider("生成する組合数", 1, 20, 5)

# 추천 생성 버튼
if st.sidebar.button("🎲 番号を生成"):
    from src.analyze import generate_recommendations
    rec_df = generate_recommendations(
        df_all, mode=rec_mode, n_combinations=n_rec, recent_n=recent_n
    )
    st.session_state["recommendations"] = rec_df
    send_ga4_event("recommendations_generated", {
        "mode": rec_mode,
        "count": n_rec
    })

# フィルタリング (r_range 는 (min, max) 튜플)
mask = (df_all["round"] >= r_range[0]) & (df_all["round"] <= r_range[1])
df_filtered = df_all[mask]
send_ga4_event("filter_applied", {
    "round_from": r_range[0], "round_to": r_range[1]
})

# ── 탭 구성 ──────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 番号頻度", "🔗 組合分析", "💰 当せん金推移", "🎲 番号推薦", "📋 データテーブル"]
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

with tab2:
    st.subheader("同時出現ペア頻度 (ヒートマップ)")
    html = load_chart_html("pair_heatmap")
    if html:
        components.html(html, height=600, scrolling=True)
        send_ga4_event("chart_viewed", {"chart_type": "pair_heatmap"})

with tab3:
    st.subheader("1 等当せん金額推移")
    html = load_chart_html("jackpot_trend")
    if html:
        components.html(html, height=500, scrolling=True)
        send_ga4_event("chart_viewed", {"chart_type": "jackpot_trend"})

with tab4:
    st.subheader("🎲 番号推薦 (統計的パターンに基づく参考値)")
    st.caption(
        "この推薦は過去の統計データ (出現頻度、ホット/コールド、"
        "合計値の分布など) に基づいて生成されます。"
        "当選を保証するものではありません。"
    )
    if "recommendations" in st.session_state:
        rec_df = st.session_state["recommendations"]
        st.dataframe(
            rec_df[["combination_id", "n1", "n2", "n3", "n4", "n5", "n6", "bonus", "mode"]],
            use_container_width=True,
            hide_index=True
        )
        send_ga4_event("chart_viewed", {"chart_type": "recommendations"})
    else:
        st.info("左のサイドバーで推薦モードを選択し、「🎲 番号を生成」ボタンを押してください。")

with tab5:
    st.subheader("抽せんデータ一覧")
    st.dataframe(df_filtered, use_container_width=True)
