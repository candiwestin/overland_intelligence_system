"""
Phase 4 validation — question_suggester tested with mock LLM and fallback logic.
Run with: pytest tests/test_question_suggester.py -v
"""
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "sample_data" / "hde_overland_sales_2022_2024.csv"


def make_mock_llm(questions: list[str]):
    """Returns a mock LLM that responds with the given questions as JSON."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(
        content=json.dumps(questions)
    )
    return mock


def test_returns_five_questions():
    from agents.question_suggester import generate_suggested_questions
    mock_questions = [
        "Is the Baja segment growing fast enough to justify dedicated product lines?",
        "Which regions are underperforming relative to their population and income levels?",
        "What event influences correlate most strongly with high-value transactions?",
        "How does customer age bracket affect average transaction value by build category?",
        "Which vehicle platforms show the strongest year-over-year revenue growth?",
    ]
    llm = make_mock_llm(mock_questions)
    result = generate_suggested_questions(SAMPLE_CSV, llm)
    assert len(result) == 5
    assert all(isinstance(q, str) for q in result)
    assert all(len(q) > 10 for q in result)


def test_questions_are_strings():
    from agents.question_suggester import generate_suggested_questions
    mock_questions = [f"Question {i}?" for i in range(5)]
    llm = make_mock_llm(mock_questions)
    result = generate_suggested_questions(SAMPLE_CSV, llm)
    assert all(isinstance(q, str) for q in result)


def test_fallback_on_llm_failure():
    from agents.question_suggester import generate_suggested_questions
    mock = MagicMock()
    mock.invoke.side_effect = Exception("LLM unavailable")
    result = generate_suggested_questions(SAMPLE_CSV, mock)
    assert len(result) >= 1
    assert all(isinstance(q, str) for q in result)


def test_fallback_questions_directly():
    from agents.question_suggester import _fallback_questions
    from tools.data_tools import load_dataframe, clean_dataframe, profile_dataframe
    df = load_dataframe(SAMPLE_CSV)
    df = clean_dataframe(df)
    profile = profile_dataframe(df)
    questions = _fallback_questions(profile)
    assert len(questions) == 5
    assert all(isinstance(q, str) for q in questions)


def test_handles_markdown_fenced_response():
    from agents.question_suggester import generate_suggested_questions
    mock_questions = [f"Question {i}?" for i in range(5)]
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(
        content=f"```json\n{json.dumps(mock_questions)}\n```"
    )
    result = generate_suggested_questions(SAMPLE_CSV, mock)
    assert len(result) == 5


def test_truncates_to_five_if_more_returned():
    from agents.question_suggester import generate_suggested_questions
    mock_questions = [f"Question {i}?" for i in range(10)]
    llm = make_mock_llm(mock_questions)
    result = generate_suggested_questions(SAMPLE_CSV, llm)
    assert len(result) == 5