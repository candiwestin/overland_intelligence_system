import sys
from pathlib import Path
from typing import TypedDict, Annotated
import operator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# -----------------------------------------------------------------------------
# State schema
# -----------------------------------------------------------------------------

class BIAgentState(TypedDict):
    # Inputs
    uploaded_file_path:  str
    business_question:   str
    supporting_docs:     list[str]

    # Data analyst outputs
    data_profile:        dict
    data_findings:       list[str]
    data_summary:        str
    data_health_score:   int

    # Question suggester outputs
    suggested_questions: list[str]

    # Research agent outputs
    search_results:      list[dict]
    rag_context:         list[str]
    market_findings:     list[str]
    market_summary:      str
    market_gaps:         list[str]

    # Insights agent outputs
    recommendations:     list[dict]
    opportunities:       list[str]
    gaps:                list[str]
    executive_summary:   str
    confidence_score:    int

    # Report outputs
    report_markdown:     str
    report_pdf_path:     str

    # Runtime
    vector_store:        object
    status:              str
    errors:              Annotated[list[str], operator.add]


# -----------------------------------------------------------------------------
# Graph construction
# -----------------------------------------------------------------------------

def build_graph(llm, embeddings, search_provider: str = None):
    """
    Builds and compiles the LangGraph pipeline.

    Nodes run sequentially:
        ingest_rag → data_analyst → research → insights → done

    The question suggester runs separately on file upload (not in the graph)
    since it fires immediately and independently of the main pipeline run.

    Args:
        llm:             LangChain chat model from llm_factory.get_llm()
        embeddings:      LangChain embeddings from embedding_factory.get_embeddings()
        search_provider: Optional override — 'tavily' or 'duckduckgo'

    Returns:
        Compiled LangGraph StateGraph ready to invoke.
    """
    from langgraph.graph import StateGraph, END

    graph = StateGraph(BIAgentState)

    # Node definitions — each wraps an agent with consistent state in/out
    graph.add_node("ingest_rag",    _make_ingest_node(embeddings))
    graph.add_node("data_analyst",  _make_data_analyst_node(llm))
    graph.add_node("research",      _make_research_node(llm, search_provider))
    graph.add_node("insights",      _make_insights_node(llm))

    # Linear pipeline — no branching in v1
    graph.set_entry_point("ingest_rag")
    graph.add_edge("ingest_rag",   "data_analyst")
    graph.add_edge("data_analyst", "research")
    graph.add_edge("research",     "insights")
    graph.add_edge("insights",     END)

    return graph.compile()


# -----------------------------------------------------------------------------
# Node factories — return functions that take and return state
# -----------------------------------------------------------------------------

def _make_ingest_node(embeddings):
    """
    Ingests supporting documents into Qdrant in-memory.
    Skips silently if no supporting docs were uploaded.
    """
    def ingest_rag(state: BIAgentState) -> dict:
        from rag.ingest import ingest_documents

        docs = state.get("supporting_docs", [])
        if not docs:
            return {"vector_store": None, "status": "rag_skipped"}

        try:
            vector_store = ingest_documents(docs, embeddings)
            return {"vector_store": vector_store, "status": "rag_complete"}
        except Exception as e:
            return {
                "vector_store": None,
                "status": "rag_failed",
                "errors": [f"RAG ingest failed: {str(e)}"],
            }

    return ingest_rag


def _make_data_analyst_node(llm):
    """
    Loads, profiles, and analyzes the uploaded CSV.
    """
    def data_analyst(state: BIAgentState) -> dict:
        from agents.data_analyst import run_data_analyst

        try:
            result = run_data_analyst(state["uploaded_file_path"], llm)
            return {
                "data_profile":      result["data_profile"],
                "data_findings":     result["data_findings"],
                "data_summary":      result["data_summary"],
                "data_health_score": result["data_health_score"],
                "status":            "data_analyst_complete",
            }
        except Exception as e:
            return {
                "data_profile":      {},
                "data_findings":     [],
                "data_summary":      "",
                "data_health_score": 0,
                "status":            "data_analyst_failed",
                "errors":            [f"Data analyst failed: {str(e)}"],
            }

    return data_analyst


def _make_research_node(llm, search_provider):
    """
    Runs market research — search + RAG retrieval + LLM synthesis.
    """
    def research(state: BIAgentState) -> dict:
        from agents.research_agent import run_research_agent

        try:
            updated = run_research_agent(dict(state), llm, search_provider)
            return {
                "search_results":  updated.get("search_results", []),
                "rag_context":     updated.get("rag_context", []),
                "market_findings": updated.get("market_findings", []),
                "market_summary":  updated.get("market_summary", ""),
                "market_gaps":     updated.get("market_gaps", []),
                "status":          "research_complete",
            }
        except Exception as e:
            return {
                "search_results":  [],
                "rag_context":     [],
                "market_findings": [],
                "market_summary":  "",
                "market_gaps":     [],
                "status":          "research_failed",
                "errors":          [f"Research agent failed: {str(e)}"],
            }

    return research


def _make_insights_node(llm):
    """
    Synthesizes all findings into ranked recommendations.
    """
    def insights(state: BIAgentState) -> dict:
        from agents.insights_agent import run_insights_agent

        try:
            updated = run_insights_agent(dict(state), llm)
            return {
                "recommendations":   updated.get("recommendations", []),
                "opportunities":     updated.get("opportunities", []),
                "gaps":              updated.get("gaps", []),
                "executive_summary": updated.get("executive_summary", ""),
                "confidence_score":  updated.get("confidence_score", 0),
                "status":            "insights_complete",
            }
        except Exception as e:
            return {
                "recommendations":   [],
                "opportunities":     [],
                "gaps":              [],
                "executive_summary": "",
                "confidence_score":  0,
                "status":            "insights_failed",
                "errors":            [f"Insights agent failed: {str(e)}"],
            }

    return insights


# -----------------------------------------------------------------------------
# Pipeline runner — convenience wrapper used by app.py
# -----------------------------------------------------------------------------

def run_pipeline(
    uploaded_file_path: str,
    business_question: str,
    llm,
    embeddings,
    supporting_docs: list[str] = None,
    search_provider: str = None,
) -> BIAgentState:
    """
    Convenience wrapper that builds the graph, sets initial state,
    and runs the full pipeline in one call.

    Args:
        uploaded_file_path: Path to the uploaded CSV or Excel file.
        business_question:  The question the user wants answered.
        llm:                LangChain chat model.
        embeddings:         LangChain embeddings.
        supporting_docs:    Optional list of file paths for RAG context.
        search_provider:    Optional search provider override.

    Returns:
        Final BIAgentState with all fields populated.
    """
    graph = build_graph(llm, embeddings, search_provider)

    initial_state: BIAgentState = {
        "uploaded_file_path":  uploaded_file_path,
        "business_question":   business_question,
        "supporting_docs":     supporting_docs or [],
        "data_profile":        {},
        "data_findings":       [],
        "data_summary":        "",
        "data_health_score":   0,
        "suggested_questions": [],
        "search_results":      [],
        "rag_context":         [],
        "market_findings":     [],
        "market_summary":      "",
        "market_gaps":         [],
        "recommendations":     [],
        "opportunities":       [],
        "gaps":                [],
        "executive_summary":   "",
        "confidence_score":    0,
        "report_markdown":     "",
        "report_pdf_path":     "",
        "vector_store":        None,
        "status":              "starting",
        "errors":              [],
    }

    return graph.invoke(initial_state)