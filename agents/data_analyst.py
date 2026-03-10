import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.data_tools import (
    load_dataframe,
    clean_dataframe,
    profile_dataframe,
    get_revenue_by_dimension,
    get_trend_by_period,
    get_top_performers,
    get_growth_rates,
)
from prompts.data_analyst_prompt import DATA_ANALYST_SYSTEM, DATA_ANALYST_USER
from tools.exceptions import DataIngestionError, LLMProviderError


def run_data_analyst(file_source, llm) -> dict:
    """
    Loads, cleans, profiles, and analyzes the uploaded data file.

    Args:
        file_source: File path or Streamlit UploadedFile object.
        llm: LangChain chat model instance from llm_factory.get_llm().

    Returns:
        dict with keys:
            data_profile      — full profile dict from profile_dataframe()
            data_findings     — list of finding strings from LLM analysis
            data_summary      — plain English summary string
            anomalies         — list of anomaly strings
            data_quality_notes — list of quality note strings
            recommended_deep_dives — list of follow-up question strings
            data_health_score — int 0-100

    Raises:
        DataIngestionError: If the file cannot be loaded or is empty.
        LLMProviderError:   If the LLM call fails.
    """
    # Load and clean
    df = load_dataframe(file_source)
    df = clean_dataframe(df)

    # Profile
    profile = profile_dataframe(df)

    # Pre-compute analysis helpers to give the LLM richer context
    revenue_by_build   = get_revenue_by_dimension(df, "build_category")
    revenue_by_region  = get_revenue_by_dimension(df, "region")
    revenue_by_year    = get_trend_by_period(df, "year")
    baja_growth        = get_growth_rates(df, "build_category")
    top_vehicles       = get_top_performers(df, "vehicle_platform", n=5)

    # Build prompt
    user_message = DATA_ANALYST_USER.format(
        shape=json.dumps(profile["shape"], indent=2),
        columns=json.dumps(profile["columns"], indent=2),
        numeric_summary=json.dumps(profile["numeric_summary"], indent=2),
        categorical_summary=json.dumps(profile["categorical_summary"], indent=2),
        date_range=json.dumps(profile["date_range"], indent=2),
        revenue_by_build_category=json.dumps(revenue_by_build, indent=2),
        revenue_by_region=json.dumps(revenue_by_region, indent=2),
        revenue_by_year=json.dumps(revenue_by_year, indent=2),
        baja_growth_rates=json.dumps(baja_growth, indent=2),
        top_vehicles=json.dumps(top_vehicles, indent=2),
        data_health_score=profile["data_health_score"],
    )

    # LLM call
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        response = llm.invoke([
            SystemMessage(content=DATA_ANALYST_SYSTEM),
            HumanMessage(content=user_message),
        ])
        raw = response.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        analysis = json.loads(raw)

    except LLMProviderError:
        raise
    except json.JSONDecodeError as e:
        raise LLMProviderError(
            provider="unknown",
            detail=f"LLM returned invalid JSON: {str(e)}"
        )
    except Exception as e:
        raise LLMProviderError(provider="unknown", detail=str(e))

    return {
        "data_profile":             profile,
        "data_findings":            analysis.get("findings", []),
        "data_summary":             analysis.get("summary", ""),
        "anomalies":                analysis.get("anomalies", []),
        "data_quality_notes":       analysis.get("data_quality_notes", []),
        "recommended_deep_dives":   analysis.get("recommended_deep_dives", []),
        "data_health_score":        profile["data_health_score"],
    }