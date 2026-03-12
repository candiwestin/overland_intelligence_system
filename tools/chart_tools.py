import io
import base64
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — safe for server and CI
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# Consistent palette across all charts — matches light dashboard theme
PALETTE = {
    "accent":       "#0077CC",   # Strong blue — primary bars/lines
    "purple":       "#6B3FBF",   # Medium purple — secondary series
    "blue_light":   "#5BA8E8",   # Lighter blue — tertiary
    "purple_light": "#9B7FD4",   # Lighter purple
    "teal":         "#1A9A8A",   # Teal — fifth category
    "background":   "#FFFFFF",   # White panel background
    "bg_raised":    "#F0F2F8",   # Soft page background
    "text":         "#1A1E2E",   # Near-black text
    "text_dim":     "#6B7280",   # Gray labels
    "grid":         "#E2E6F0",   # Subtle grid lines
    "border":       "#D0D6E8",   # Panel borders
}

CHART_STYLE = {
    "figure.facecolor":  PALETTE["background"],
    "axes.facecolor":    PALETTE["bg_raised"],
    "axes.edgecolor":    PALETTE["border"],
    "axes.labelcolor":   PALETTE["text_dim"],
    "xtick.color":       PALETTE["text_dim"],
    "ytick.color":       PALETTE["text_dim"],
    "text.color":        PALETTE["text"],
    "grid.color":        PALETTE["grid"],
    "grid.linestyle":    "--",
    "grid.alpha":        0.8,
}


def revenue_by_year_chart(df: pd.DataFrame) -> str:
    """
    Bar chart — total revenue by year.
    Returns base64-encoded PNG string for embedding in reports and dashboard.
    """
    if "total_revenue" not in df.columns or "year" not in df.columns:
        return ""

    data = df.groupby("year")["total_revenue"].sum().sort_index()

    with plt.rc_context(CHART_STYLE):
        fig, ax = plt.subplots(figsize=(8, 4))
        bars = ax.bar(
            data.index.astype(str),
            data.values,
            color=PALETTE["accent"],
            edgecolor=PALETTE["background"],
            linewidth=0.8,
        )
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"${x/1_000_000:.1f}M" if x >= 1_000_000 else f"${x/1_000:.0f}K"
        ))
        ax.set_title("Revenue by Year", fontsize=13, pad=12, color=PALETTE["text"], fontweight="bold")
        ax.set_xlabel("Year", color=PALETTE["text_dim"])
        ax.set_ylabel("Total Revenue", color=PALETTE["text_dim"])
        ax.grid(axis="y")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        return _fig_to_base64(fig)


def revenue_by_build_category_chart(df: pd.DataFrame) -> str:
    """
    Horizontal bar chart — revenue by build category, sorted descending.
    Highlights the baja_prerunner bar in purple accent.
    """
    if "total_revenue" not in df.columns or "build_category" not in df.columns:
        return ""

    data = df.groupby("build_category")["total_revenue"].sum().sort_values()

    colors = [
        PALETTE["purple"] if "baja" in str(cat).lower() else PALETTE["accent"]
        for cat in data.index
    ]

    with plt.rc_context(CHART_STYLE):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(data.index, data.values, color=colors, edgecolor=PALETTE["background"])
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"${x/1_000_000:.1f}M" if x >= 1_000_000 else f"${x/1_000:.0f}K"
        ))
        ax.set_title("Revenue by Build Category", fontsize=13, pad=12, color=PALETTE["text"], fontweight="bold")
        ax.set_xlabel("Total Revenue", color=PALETTE["text_dim"])
        ax.grid(axis="x")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
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
            color=PALETTE["purple"], marker="o", linewidth=2.5, label="Baja / Pre-runner",
        )
        ax.plot(
            other.index.astype(str), other.values,
            color=PALETTE["accent"], marker="o", linewidth=2.5, label="All Other Builds",
        )
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(
            lambda x, _: f"${x/1_000_000:.1f}M" if x >= 1_000_000 else f"${x/1_000:.0f}K"
        ))
        ax.set_title("Baja vs Other Builds — Revenue Trend", fontsize=13, pad=12, color=PALETTE["text"], fontweight="bold")
        ax.set_xlabel("Year", color=PALETTE["text_dim"])
        ax.set_ylabel("Total Revenue", color=PALETTE["text_dim"])
        ax.legend(facecolor=PALETTE["background"], edgecolor=PALETTE["border"], labelcolor=PALETTE["text"])
        ax.grid()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
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
        PALETTE["accent"],
        PALETTE["purple"],
        PALETTE["blue_light"],
        PALETTE["purple_light"],
        PALETTE["teal"],
    ]

    with plt.rc_context(CHART_STYLE):
        fig, ax = plt.subplots(figsize=(7, 5))
        fig.patch.set_facecolor(PALETTE["background"])
        wedges, texts, autotexts = ax.pie(
            data.values,
            labels=data.index,
            autopct="%1.1f%%",
            colors=region_colors[:len(data)],
            startangle=140,
            wedgeprops={"edgecolor": PALETTE["background"], "linewidth": 1.5},
        )
        for t in texts:
            t.set_color(PALETTE["text"])
            t.set_fontsize(10)
        for t in autotexts:
            t.set_color(PALETTE["background"])
            t.set_fontsize(9)
            t.set_fontweight("bold")
        ax.set_title("Revenue by Region", fontsize=13, pad=12, color=PALETTE["text"], fontweight="bold")
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
        "revenue_by_year":           revenue_by_year_chart(df),
        "revenue_by_build_category": revenue_by_build_category_chart(df),
        "baja_growth_trend":         baja_growth_trend_chart(df),
        "revenue_by_region":         revenue_by_region_chart(df),
    }


def _fig_to_base64(fig) -> str:
    """Converts a matplotlib figure to a base64-encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor=PALETTE["background"])
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")