import io
import base64
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — safe for Streamlit and CI
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# Consistent palette across all charts
PALETTE = {
    "baja":       "#D4431A",   # Burnt orange — Baja/pre-runner
    "overland":   "#39FF14",   # Tactical green — overlanding
    "neutral":    "#C8B560",   # Instrument gold — neutral/mixed
    "background": "#0A0E0A",   # Near-black
    "text":       "#D6DDD0",   # Aged white
    "grid":       "#1E241E",   # Subtle grid
}

CHART_STYLE = {
    "figure.facecolor":  PALETTE["background"],
    "axes.facecolor":    PALETTE["background"],
    "axes.edgecolor":    PALETTE["grid"],
    "axes.labelcolor":   PALETTE["text"],
    "xtick.color":       PALETTE["text"],
    "ytick.color":       PALETTE["text"],
    "text.color":        PALETTE["text"],
    "grid.color":        PALETTE["grid"],
    "grid.linestyle":    "--",
    "grid.alpha":        0.5,
}


def revenue_by_year_chart(df: pd.DataFrame) -> str:
    """
    Bar chart — total revenue by year.
    Returns base64-encoded PNG string for embedding in reports and Streamlit.
    """
    if "total_revenue" not in df.columns or "year" not in df.columns:
        return ""

    data = df.groupby("year")["total_revenue"].sum().sort_index()

    with plt.rc_context(CHART_STYLE):
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.bar(
            data.index.astype(str),
            data.values,
            color=PALETTE["neutral"],
            edgecolor=PALETTE["background"],
            linewidth=0.8,
        )
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"${x/1_000_000:.1f}M" if x >= 1_000_000 else f"${x/1_000:.0f}K"
        ))
        ax.set_title("Revenue by Year", fontsize=13, pad=12)
        ax.set_xlabel("Year")
        ax.set_ylabel("Total Revenue")
        ax.grid(axis="y")
        fig.tight_layout()
        return _fig_to_base64(fig)


def revenue_by_build_category_chart(df: pd.DataFrame) -> str:
    """
    Horizontal bar chart — revenue by build category, sorted descending.
    Highlights the baja_prerunner bar in the accent color.
    """
    if "total_revenue" not in df.columns or "build_category" not in df.columns:
        return ""

    data = df.groupby("build_category")["total_revenue"].sum().sort_values()

    colors = [
        PALETTE["baja"] if "baja" in str(cat).lower() else PALETTE["neutral"]
        for cat in data.index
    ]

    with plt.rc_context(CHART_STYLE):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(data.index, data.values, color=colors, edgecolor=PALETTE["background"])
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"${x/1_000_000:.1f}M" if x >= 1_000_000 else f"${x/1_000:.0f}K"
        ))
        ax.set_title("Revenue by Build Category", fontsize=13, pad=12)
        ax.set_xlabel("Total Revenue")
        ax.grid(axis="x")
        fig.tight_layout()
        return _fig_to_base64(fig)


def baja_growth_trend_chart(df: pd.DataFrame) -> str:
    """
    Line chart — Baja vs rest-of-portfolio revenue by year.
    This is the money chart — directly addresses the demo business question.
    """
    if "total_revenue" not in df.columns or "year" not in df.columns \
            or "build_category" not in df.columns:
        return ""

    baja = (
        df[df["build_category"] == "baja_prerunner"]
        .groupby("year")["total_revenue"].sum()
    )
    other = (
        df[df["build_category"] != "baja_prerunner"]
        .groupby("year")["total_revenue"].sum()
    )

    with plt.rc_context(CHART_STYLE):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(
            baja.index.astype(str), baja.values,
            color=PALETTE["baja"], marker="o", linewidth=2.5, label="Baja / Pre-runner",
        )
        ax.plot(
            other.index.astype(str), other.values,
            color=PALETTE["neutral"], marker="o", linewidth=2.5, label="All Other Builds",
        )
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"${x/1_000_000:.1f}M" if x >= 1_000_000 else f"${x/1_000:.0f}K"
        ))
        ax.set_title("Baja vs Other Builds — Revenue Trend", fontsize=13, pad=12)
        ax.set_xlabel("Year")
        ax.set_ylabel("Total Revenue")
        ax.legend(facecolor=PALETTE["background"], edgecolor=PALETTE["grid"])
        ax.grid()
        fig.tight_layout()
        return _fig_to_base64(fig)


def revenue_by_region_chart(df: pd.DataFrame) -> str:
    """
    Pie chart — revenue share by region.
    """
    if "total_revenue" not in df.columns or "region" not in df.columns:
        return ""

    data = df.groupby("region")["total_revenue"].sum().sort_values(ascending=False)

    region_colors = [
        PALETTE["baja"], PALETTE["neutral"], "#4A7C59", "#6B8F71", "#9CAF88"
    ]

    with plt.rc_context(CHART_STYLE):
        fig, ax = plt.subplots(figsize=(7, 5))
        wedges, texts, autotexts = ax.pie(
            data.values,
            labels=data.index,
            autopct="%1.1f%%",
            colors=region_colors[:len(data)],
            startangle=140,
            wedgeprops={"edgecolor": PALETTE["background"], "linewidth": 1.2},
        )
        for t in texts:
            t.set_color(PALETTE["text"])
        for t in autotexts:
            t.set_color(PALETTE["background"])
            t.set_fontsize(9)
        ax.set_title("Revenue by Region", fontsize=13, pad=12)
        fig.tight_layout()
        return _fig_to_base64(fig)


def generate_all_charts(df: pd.DataFrame) -> dict[str, str]:
    """
    Generates all standard charts for the report.

    Returns:
        Dict of chart_name -> base64 PNG string.
        Empty string values indicate a chart could not be generated
        (missing columns, etc.).
    """
    return {
        "revenue_by_year":          revenue_by_year_chart(df),
        "revenue_by_build_category": revenue_by_build_category_chart(df),
        "baja_growth_trend":        baja_growth_trend_chart(df),
        "revenue_by_region":        revenue_by_region_chart(df),
    }


def _fig_to_base64(fig) -> str:
    """Converts a matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor=PALETTE["background"])
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")