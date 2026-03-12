
# Research agent


import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.search_factory import get_search_client
from tools.search_tools import run_multi_search
from rag.retriever import build_context_block
from prompts.research_prompt import RESEARCH_SYSTEM, RESEARCH_USER
from tools.exceptions import SearchProviderError, LLMProviderError


def run_research_agent(state: dict, llm, search_provider: str = None) -> dict:
    """
    Executes market research for the business question.

    Runs multi-query search, retrieves RAG context from uploaded docs,
    then synthesizes everything into structured market findings via LLM.

    Args:
        state:           BIAgentState dict. Reads:
                           - business_question
                           - data_findings
                           - supporting_docs (list of file paths, may be empty)
                         Writes back to state and returns updated copy.
        llm:             LangChain chat model from llm_factory.get_llm().
        search_provider: Optional provider override ('tavily', 'duckduckgo').
                         Falls back to settings default if not provided.

    Returns:
        Updated state dict with keys added:
            - search_results:   list of raw result dicts
            - rag_context:      list of retrieved chunk strings
            - market_findings:  list of finding strings
            - market_summary:   plain English summary string
            - market_gaps:      list of gap/opportunity strings
    """
    business_question = state.get("business_question", "")
    data_findings = state.get("data_findings", [])
    vector_store = state.get("vector_store", None)

    # Build search queries from the business question
    queries = _build_search_queries(business_question, data_findings)

    # Search — fallback is handled automatically by the registry
    search_results = []
    try:
        client = get_search_client(search_provider)
        search_results = run_multi_search(client, queries)
    except SearchProviderError as e:
        state.setdefault("errors", []).append(
            e.retry_message or str(e)
        )

    # RAG context from uploaded supporting documents
    rag_chunks = []
    if vector_store is not None:
        rag_chunks = [
            build_context_block(vector_store, q) for q in queries
        ]
        rag_chunks = [c for c in rag_chunks if c]

    # Format inputs for the LLM prompt
    search_text = _format_search_results(search_results)
    rag_text = "\n\n---\n\n".join(rag_chunks) if rag_chunks else "No supporting documents uploaded."
    findings_text = "\n".join(f"- {f}" for f in data_findings) if data_findings else "No internal findings yet."

    user_message = RESEARCH_USER.format(
        business_question=business_question,
        data_findings=findings_text,
        search_results=search_text,
        rag_context=rag_text,
    )

    # LLM synthesis
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        response = llm.invoke([
            SystemMessage(content=RESEARCH_SYSTEM),
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

    state["search_results"]  = search_results
    state["rag_context"]     = rag_chunks
    state["market_findings"] = analysis.get("market_findings", [])
    state["market_summary"]  = analysis.get("market_summary", "")
    state["market_gaps"]     = analysis.get("market_gaps", [])

    return state


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _build_search_queries(business_question: str, data_findings: list[str]) -> list[str]:
    """
    Derives 3 targeted search queries from the business question
    and any data findings that suggest specific research angles.

    Keeps queries short and specific — better search signal.
    """
    queries = []

    # Primary — the question itself, trimmed
    primary = business_question.strip()
    if len(primary) > 120:
        primary = primary[:120]
    queries.append(primary)

    # Secondary — extract key nouns from the question for a tighter query
    secondary = _extract_search_keywords(business_question)
    if secondary and secondary != primary:
        queries.append(secondary)

    # Tertiary — if data findings mention a segment, anchor a query on it
    if data_findings:
        for finding in data_findings[:3]:
            if any(kw in finding.lower() for kw in ["baja", "pre-runner", "region", "growth"]):
                kw_query = _extract_search_keywords(finding)
                if kw_query and kw_query not in queries:
                    queries.append(kw_query)
                    break

    return queries[:4]


def _extract_search_keywords(text: str) -> str:
    """
    Strips common stop words and returns a condensed keyword string
    suitable for a search query.
    """
    stop_words = {
        "is", "the", "a", "an", "and", "or", "but", "in", "on", "at",
        "to", "for", "of", "with", "by", "from", "as", "are", "was",
        "be", "been", "being", "have", "has", "had", "do", "does", "did",
        "will", "would", "could", "should", "may", "might", "shall",
        "which", "that", "this", "these", "those", "it", "its",
        "enough", "still", "just", "our", "we", "us", "they", "their",
    }
    words = text.lower().replace("?", "").replace(",", "").split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return " ".join(keywords[:8])


def _format_search_results(results: list[dict]) -> str:
    """
    Formats raw search results into a readable block for the LLM prompt.
    Caps at 8 results to keep the context window manageable.
    """
    if not results:
        return "No search results available."

    parts = []
    for i, r in enumerate(results[:8], 1):
        title = r.get("title", "")
        content = r.get("content", "")
        url = r.get("url", "")
        parts.append(
            f"[Result {i}]{' — ' + title if title else ''}\n"
            f"{content[:600]}\n"
            f"{url}"
        )

    return "\n\n".join(parts)