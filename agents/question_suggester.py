import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.data_tools import load_dataframe, clean_dataframe, profile_dataframe
from prompts.question_suggester_prompt import (
    QUESTION_SUGGESTER_SYSTEM,
    QUESTION_SUGGESTER_USER,
)
from tools.exceptions import LLMProviderError, DataIngestionError
from config.settings import settings


def generate_suggested_questions(file_source, llm) -> list[str]:
    """
    Fires immediately on CSV upload. Reads the data profile and returns
    5 dynamic business questions specific to the uploaded dataset.

    This is a single focused LLM call — not a full pipeline invocation.
    Designed to be fast (2-3 seconds on Groq).

    Args:
        file_source: File path or Streamlit UploadedFile object.
        llm: LangChain chat model instance from llm_factory.get_llm().

    Returns:
        List of exactly 5 question strings.
        Falls back to default questions if LLM call fails — never blocks the UI.

    Raises:
        DataIngestionError: If the file cannot be loaded.
    """
    # Load and profile — reuse the same tools as the data analyst
    df = load_dataframe(file_source)
    df = clean_dataframe(df)
    profile = profile_dataframe(df)

    # Build a lean prompt — only what the LLM needs to generate questions
    columns_summary = {
        col: data["dtype"]
        for col, data in profile["columns"].items()
    }

    user_message = QUESTION_SUGGESTER_USER.format(
        columns=json.dumps(columns_summary, indent=2),
        categorical_summary=json.dumps(profile["categorical_summary"], indent=2),
        numeric_summary=json.dumps(profile["numeric_summary"], indent=2),
        date_range=json.dumps(profile["date_range"], indent=2),
    )

    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        response = llm.invoke([
            SystemMessage(content=QUESTION_SUGGESTER_SYSTEM),
            HumanMessage(content=user_message),
        ])
        raw = response.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        questions = json.loads(raw)

        # Validate — must be a list of strings
        if not isinstance(questions, list):
            raise ValueError("LLM did not return a list")
        questions = [str(q) for q in questions if q]

        # Enforce exactly N questions from settings
        n = settings.suggested_question_count
        return questions[:n] if len(questions) >= n else questions

    except LLMProviderError:
        raise
    except Exception:
        # Never block the UI on a question suggestion failure
        # Return sensible defaults based on common column patterns
        return _fallback_questions(profile)


def _fallback_questions(profile: dict) -> list[str]:
    """
    Returns generic but useful fallback questions when the LLM call fails.
    Based on detected column patterns in the profile.
    """
    cols = set(profile["columns"].keys())
    questions = []

    if "total_revenue" in cols and "year" in cols:
        questions.append("Which year showed the strongest revenue growth and what drove it?")
    if "region" in cols:
        questions.append("Which regions are underperforming relative to their market potential?")
    if "build_category" in cols or "vehicle_platform" in cols:
        questions.append("Which product categories have the highest revenue per transaction?")
    if "customer_age_bracket" in cols:
        questions.append("How does purchasing behavior differ across customer age groups?")
    if "event_influence" in cols:
        questions.append("What impact do industry events have on sales volume and category mix?")

    # Pad with generic fallbacks if needed
    generic = [
        "What are the top revenue drivers and how have they trended over time?",
        "Where are the biggest gaps between current performance and market opportunity?",
        "Which customer segments show the highest growth potential?",
        "What seasonal patterns exist and how should inventory strategy reflect them?",
        "Which product lines warrant dedicated investment based on growth trajectory?",
    ]

    for q in generic:
        if len(questions) >= settings.suggested_question_count:
            break
        if q not in questions:
            questions.append(q)

    return questions[:settings.suggested_question_count]