import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prompts.report_prompt import REPORT_SYSTEM, REPORT_USER
from tools.exceptions import LLMProviderError


def run_report_agent(state: dict, llm) -> dict:
    """
    Generates the final Markdown intelligence report from the completed state.

    Args:
        state: BIAgentState dict. Reads all accumulated findings.
        llm:   LangChain chat model from llm_factory.get_llm().

    Returns:
        Updated state dict with:
            - report_markdown: str — full Markdown report
            - status:          'report_complete' or 'report_failed'
    """
    business_question = state.get("business_question", "")
    executive_summary = state.get("executive_summary", "")
    data_findings     = state.get("data_findings", [])
    market_findings   = state.get("market_findings", [])
    recommendations   = state.get("recommendations", [])
    opportunities     = state.get("opportunities", [])
    data_health_score = state.get("data_health_score", 0)

    def bullets(items):
        return "\n".join(f"- {i}" for i in items) if items else "None available."

    def format_recommendations(recs):
        if not recs:
            return "None available."
        lines = []
        for r in recs:
            action    = r.get("action", "")
            rationale = r.get("rationale", "")
            priority  = r.get("priority", "medium")
            timeframe = r.get("timeframe", "short_term")
            lines.append(
                f"{r.get('rank', '?')}. **{action}** "
                f"[{priority.upper()} / {timeframe.replace('_', ' ')}]\n   {rationale}"
            )
        return "\n".join(lines)

    user_message = REPORT_USER.format(
        business_question=business_question,
        executive_summary=executive_summary,
        data_findings=bullets(data_findings),
        market_findings=bullets(market_findings),
        recommendations=format_recommendations(recommendations),
        opportunities=bullets(opportunities),
        data_health_score=data_health_score,
    )

    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        response = llm.invoke([
            SystemMessage(content=REPORT_SYSTEM),
            HumanMessage(content=user_message),
        ])
        report_markdown = response.content.strip()

        # Strip accidental code fences if LLM wraps in markdown block
        if report_markdown.startswith("```"):
            lines = report_markdown.split("\n")
            report_markdown = "\n".join(lines[1:-1]).strip()

    except LLMProviderError:
        raise
    except Exception as e:
        raise LLMProviderError(provider="unknown", detail=str(e))

    state["report_markdown"] = report_markdown
    state["status"] = "report_complete"
    return state