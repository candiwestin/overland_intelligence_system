import pandas as pd
import numpy as np
from pathlib import Path
from typing import Union

from tools.exceptions import DataIngestionError


# -----------------------------------------------------------------------------
# Loading
# -----------------------------------------------------------------------------

def load_dataframe(source: Union[str, Path, object]) -> pd.DataFrame:
    """
    Loads a CSV or Excel file into a DataFrame.

    Args:
        source: File path string, Path object, or a file-like object
                (str or Path).

    Returns:
        pandas DataFrame

    Raises:
        DataIngestionError: If the file cannot be parsed or is empty.
    """
    try:
        if isinstance(source, (str, Path)):
            suffix = Path(source).suffix.lower()
        else:
            name = getattr(source, "name", "")
            suffix = Path(name).suffix.lower()

        if suffix in (".xlsx", ".xls"):
            df = pd.read_excel(source)
        elif suffix == ".csv":
            df = pd.read_csv(source)
        else:
            df = pd.read_csv(source)

        if df.empty:
            raise DataIngestionError("The uploaded file contains no data.")

        return df

    except DataIngestionError:
        raise
    except Exception as e:
        raise DataIngestionError(f"Could not parse file: {str(e)}")


# -----------------------------------------------------------------------------
# Cleaning
# -----------------------------------------------------------------------------

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies standard cleaning to a raw DataFrame.

    - Strips whitespace from column names
    - Lowercases column names
    - Drops fully duplicate rows
    - Strips string whitespace from object columns
    - Parses date columns where detected

    Returns:
        Cleaned DataFrame
    """
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    original_len = len(df)
    df = df.drop_duplicates()
    dupes_dropped = original_len - len(df)

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    for col in df.columns:
        if "date" in col:
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

    df._metadata = {"dupes_dropped": dupes_dropped}
    return df


# -----------------------------------------------------------------------------
# Profiling
# -----------------------------------------------------------------------------

def profile_dataframe(df: pd.DataFrame) -> dict:
    """
    Generates a structured profile of the DataFrame for the data analyst agent.

    Returns a dict containing:
        - shape: row and column counts
        - columns: per-column type, null count, null pct, unique count
        - numeric_summary: describe() output for numeric columns
        - categorical_summary: top values for object columns
        - date_range: min/max for detected date columns
        - data_health_score: 0-100 score based on completeness and consistency
    """
    profile = {}

    profile["shape"] = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
    }

    columns = {}
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        null_pct = round(null_count / len(df) * 100, 2)
        unique_count = int(df[col].nunique())
        columns[col] = {
            "dtype": str(df[col].dtype),
            "null_count": null_count,
            "null_pct": null_pct,
            "unique_count": unique_count,
        }
    profile["columns"] = columns

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        desc = df[numeric_cols].describe().round(2)
        profile["numeric_summary"] = desc.to_dict()
    else:
        profile["numeric_summary"] = {}

    cat_cols = df.select_dtypes(include="object").columns.tolist()
    categorical_summary = {}
    for col in cat_cols:
        top = df[col].value_counts().head(5)
        categorical_summary[col] = {
            str(k): int(v) for k, v in top.items()
        }
    profile["categorical_summary"] = categorical_summary

    date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
    date_ranges = {}
    for col in date_cols:
        date_ranges[col] = {
            "min": str(df[col].min()),
            "max": str(df[col].max()),
        }
    profile["date_range"] = date_ranges

    profile["data_health_score"] = _calculate_health_score(df, columns)

    return profile


def _calculate_health_score(df: pd.DataFrame, column_profile: dict) -> int:
    """
    Calculates a 0-100 data health score based on:
    - Completeness (no nulls = higher score)
    - Row count (more data = more reliable)
    - Duplicate ratio
    """
    scores = []

    null_pcts = [col["null_pct"] for col in column_profile.values()]
    avg_null_pct = sum(null_pcts) / len(null_pcts) if null_pcts else 0
    completeness_score = max(0, 100 - avg_null_pct)
    scores.append(completeness_score)

    row_score = min(100, (df.shape[0] / 100) * 10)
    scores.append(row_score)

    dup_ratio = df.duplicated().sum() / len(df) * 100
    dup_score = max(0, 100 - dup_ratio * 2)
    scores.append(dup_score)

    return int(sum(scores) / len(scores))


# -----------------------------------------------------------------------------
# Analysis helpers
# -----------------------------------------------------------------------------

def get_revenue_by_dimension(df: pd.DataFrame, dimension: str) -> dict:
    """
    Aggregates total_revenue by a given dimension column.
    Returns sorted dict of dimension value -> revenue.
    """
    if "total_revenue" not in df.columns or dimension not in df.columns:
        return {}

    result = (
        df.groupby(dimension)["total_revenue"]
        .sum()
        .sort_values(ascending=False)
        .round(2)
    )
    return {str(k): float(v) for k, v in result.items()}


def get_trend_by_period(df: pd.DataFrame, period: str = "year") -> dict:
    """
    Aggregates total_revenue by time period.

    Args:
        period: 'year', 'quarter', or 'month'

    Returns:
        Dict of period -> revenue
    """
    if "total_revenue" not in df.columns:
        return {}

    if period == "year" and "year" in df.columns:
        col = "year"
    elif period == "quarter" and "quarter" in df.columns:
        col = "quarter"
    elif period == "month" and "month" in df.columns:
        col = "month"
    else:
        return {}

    result = (
        df.groupby(col)["total_revenue"]
        .sum()
        .sort_index()
        .round(2)
    )
    return {str(k): float(v) for k, v in result.items()}


def get_top_performers(df: pd.DataFrame, dimension: str, n: int = 5) -> dict:
    """
    Returns the top N performers by total_revenue for a given dimension.
    """
    if "total_revenue" not in df.columns or dimension not in df.columns:
        return {}

    result = (
        df.groupby(dimension)["total_revenue"]
        .sum()
        .nlargest(n)
        .round(2)
    )
    return {str(k): float(v) for k, v in result.items()}


def get_growth_rates(df: pd.DataFrame, group_col: str) -> dict:
    """
    Calculates year-over-year revenue growth rates for a given grouping column.

    Returns dict of group -> {year: revenue, yoy_growth_pct}
    """
    if "total_revenue" not in df.columns or "year" not in df.columns:
        return {}
    if group_col not in df.columns:
        return {}

    pivot = (
        df.groupby([group_col, "year"])["total_revenue"]
        .sum()
        .unstack(fill_value=0)
        .round(2)
    )

    growth = {}
    for group in pivot.index:
        row = pivot.loc[group]
        years = sorted(row.index.tolist())
        entry = {}
        for i, year in enumerate(years):
            entry[str(year)] = float(row[year])
            if i > 0:
                prev = row[years[i - 1]]
                if prev > 0:
                    pct = round(((row[year] - prev) / prev) * 100, 1)
                    entry[f"{year}_yoy_pct"] = pct
        growth[str(group)] = entry

    return growth