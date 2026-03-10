import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prompts.insights_prompt import INSIGHTS_SYSTEM, INSIGHTS_USER
from tools.exceptions import LLMProviderError


def run_insights_agent(state: dict, llm) -> dict:
    """
    Synthesizes all gathered intelligence into ranked strategic recommendations.

    This is the final analytical step before report generation. It reads
    everything accumulated in state and produces the executive-level output
    the user is actually after.

    Args:
        state: BIAgentState dict. Reads:
                 - business_question
                 - data_findings
                 - market_findings
                 - market_gaps
                 - data_health_score (from data_profile)
               Writes back to state and returns updated copy.
        llm:   LangChain chat model from llm_factory.get_llm().

    Returns:
        Updated state dict with keys added:
            - recommendations:    list of recommendation dicts
            - opportunities:      list of opportunity strings
            - gaps:               list of gap strings (carried from research)
            - executive_summary:  plain English synthesis string
            - confidence_score:   int 0-100
    """
    business_question  = state.get("business_question", "")
    data_findings      = state.get("data_findings", [])
    market_findings    = state.get("market_findings", [])
    market_gaps        = state.get("market_gaps", [])
    data_health_score  = state.get("data_health_score", 0)

    # Format lists as readable bullet points for the prompt
    def bullets(items):
        return "\n".join(f"- {i}" for i in items) if items else "None available."

    user_message = INSIGHTS_USER.format(
        business_question=business_question,
        data_findings=bullets(data_findings),
        market_findings=bullets(market_findings),
        market_gaps=bullets(market_gaps),
        data_health_score=data_health_score,
    )

    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        response = llm.invoke([
            SystemMessage(content=INSIGHTS_SYSTEM),
            HumanMessage(content=user_message),
        ])
        raw = response.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        analysis = json.loads(raw)

    except json.JSONDecodeError as e:
        raise LLMProviderError(provider="unknown", detail=f"Invalid JSON from LLM: {str(e)}")
    except LLMProviderError:
        raise
    except Exception as e:
        raise LLMProviderError(provider="unknown", detail=str(e))

    # Normalize recommendations — ensure required keys are present
    raw_recs = analysis.get("recommendations", [])
    recommendations = [_normalize_recommendation(r, i) for i, r in enumerate(raw_recs, 1)]

    state["recommendations"]   = recommendations
    state["opportunities"]     = analysis.get("opportunities", [])
    state["gaps"]              = market_gaps
    state["executive_summary"] = analysis.get("executive_summary", "")
    state["confidence_score"]  = _clamp(analysis.get("confidence_score", 50), 0, 100)

    return state


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _normalize_recommendation(rec: dict, fallback_rank: int) -> dict:
    """
    Ensures a recommendation dict has all expected keys with safe defaults.
    Protects downstream rendering from KeyErrors.
    """
    return {
        "rank":      rec.get("rank", fallback_rank),
        "action":    rec.get("action", ""),
        "rationale": rec.get("rationale", ""),
        "priority":  rec.get("priority", "medium"),
        "timeframe": rec.get("timeframe", "short_term"),
    }


def _clamp(value, min_val, max_val) -> int:
    """Clamps a numeric value to [min_val, max_val]."""
    try:
        return max(min_val, min(max_val, int(value)))
    except (TypeError, ValueError):
        return min_val