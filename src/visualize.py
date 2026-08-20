"""
visualize.py — 5種Plotlyチャート生成
出力: charts/*.html（インタラクティブ）, charts/*.png（静止画）
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

logging.basicConfig(level=logging.INFO)
CHARTS_DIR = Path("charts")
CHARTS_DIR.mkdir(exist_ok=True)


def save_chart(fig: go.Figure, name: str) -> None:
    """HTML + PNG を同時保存する。"""
    fig.write_html(CHARTS_DIR / f"{name}.html")
    fig.write_image(CHARTS_DIR / f"{name}.png", width=1200, height=600)
    logging.info("保存: charts/%s.html / .png", name)


def chart_freq_bar() -> None:
    """番号出現頻度バーチャート（hot/cold/normal 色分け）"""
    df = pd.read_csv("data/analysis/freq_all.csv", comment="#")
    df_hc = pd.read_csv("data/analysis/hot_cold.csv", comment="#")
    df = df.merge(df_hc[["number", "status"]], on="number")
    color_map = {"hot": "#E74C3C", "cold": "#3498DB", "normal": "#95A5A6"}
    df["color"] = df["status"].map(color_map)

    fig = go.Figure(go.Bar(
        x=df["number"], y=df["count"],
        marker_color=df["color"],
        hovertemplate="番号 %{x}<br>出現回数: %{y}<extra></extra>",
    ))
    fig.update_layout(
        title="ロト6 番号別出現頻度 (赤=Hot / 青=Cold)",
        xaxis_title="番号", yaxis_title="出現回数",
    )
    save_chart(fig, "freq_bar")


def chart_pair_heatmap() -> None:
    """同時出現ペア 43×43 ヒートマップ"""
    df = pd.read_csv("data/analysis/pair_matrix.csv", comment="#", index_col=0)
    df.index = df.index.astype(int)
    df.columns = df.columns.astype(int)
    fig = px.imshow(
        df,
        labels={"color": "同時出現回数", "x": "番号", "y": "番号"},
        title="ロト6 番号同時出現ペア頻度",
        color_continuous_scale="Blues",
    )
    save_chart(fig, "pair_heatmap")


def chart_jackpot_trend() -> None:
    """1等当せん金額時系列 + 20回移動平均"""
    df = pd.read_csv("data/analysis/jackpot_trend.csv", comment="#")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["round"], y=df["prize1_amount"],
        mode="lines", name="1等当せん金額",
        line=dict(color="#3498DB", width=1), opacity=0.5,
    ))
    fig.add_trace(go.Scatter(
        x=df["round"], y=df["ma20"],
        mode="lines", name="20回移動平均",
        line=dict(color="#E74C3C", width=2),
    ))
    fig.update_layout(
        title="ロト6 1等当せん金額推移",
        xaxis_title="回号", yaxis_title="当せん金額 (円)",
    )
    save_chart(fig, "jackpot_trend")


def chart_odd_even_donut() -> None:
    """奇偶・高低 全体集計ドーナツチャート"""
    df = pd.read_csv("data/analysis/odd_even_high_low.csv", comment="#")
    labels = ["奇数", "偶数", "低(1-21)", "高(22-43)"]
    values = [
        df["odd_count"].sum(), df["even_count"].sum(),
        df["low_count"].sum(), df["high_count"].sum(),
    ]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.4,
        hovertemplate="%{label}: %{value}個 (%{percent})<extra></extra>",
    ))
    fig.update_layout(title="ロト6 奇偶・高低分布")
    save_chart(fig, "odd_even_donut")


def chart_sum_histogram() -> None:
    """番号合計分布ヒストグラム + 正規分布オーバーレイ"""
    df = pd.read_csv("data/analysis/sum_distribution.csv", comment="#")
    sums = df["sum"].dropna()

    fig = px.histogram(
        df, x="sum", nbins=30, histnorm="probability density",
        title="ロト6 抽せん番号合計の分布",
        labels={"sum": "合計値", "count": "頻度"},
        color_discrete_sequence=["#3498DB"],
    )

    mu, sigma = sums.mean(), sums.std()
    x_range = np.linspace(sums.min(), sums.max(), 200)
    normal_curve = stats.norm.pdf(x_range, mu, sigma)
    fig.add_trace(go.Scatter(
        x=x_range, y=normal_curve,
        mode="lines", name=f"正規分布近似 (μ={mu:.1f}, σ={sigma:.1f})",
        line=dict(color="#E74C3C", width=2),
    ))
    fig.update_layout(yaxis_title="密度")
    save_chart(fig, "sum_histogram")


if __name__ == "__main__":
    chart_freq_bar()
    chart_pair_heatmap()
    chart_jackpot_trend()
    chart_odd_even_donut()
    chart_sum_histogram()
    logging.info("全チャート生成完了")
