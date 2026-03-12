"""
Overland Intelligence System — CLI Demo Script
High Desert Expeditions

Runs the full pipeline from the command line without the browser dashboard.
Useful for testing, recording demos, and showing the pipeline end-to-end.

Usage:
    python demo.py
    python demo.py --question "Your custom question here"
    python demo.py --llm ollama_primary --search duckduckgo
    python demo.py --no-pdf
"""
import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


# -----------------------------------------------------------------------
# CLI arguments
# -----------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Overland Intelligence System — CLI Demo"
    )
    parser.add_argument(
        "--question", "-q",
        type=str,
        default=(
            "Is the Baja and pre-runner segment growing fast enough to justify "
            "dedicated product lines, or is it still a niche within the broader "
            "overlanding market? Which vehicle platforms and regions should a "
            "gear manufacturer prioritize?"
        ),
        help="Business question to analyze",
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        default="sample_data/hde_overland_sales_2022_2024.csv",
        help="Path to CSV or Excel file",
    )
    parser.add_argument(
        "--llm",
        type=str,
        default="groq",
        choices=["groq", "ollama_primary", "ollama_secondary"],
        help="LLM provider",
    )
    parser.add_argument(
        "--search",
        type=str,
        default="duckduckgo",
        choices=["duckduckgo", "tavily"],
        help="Search provider",
    )
    parser.add_argument(
        "--no-pdf",
        action="store_true",
        help="Skip PDF generation",
    )
    return parser.parse_args()


# -----------------------------------------------------------------------
# Display helpers
# -----------------------------------------------------------------------

BLUE   = "\033[94m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
PURPLE = "\033[95m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def header(text):
    width = 68
    print(f"\n{BLUE}{'─' * width}{RESET}")
    print(f"{BOLD}{BLUE}  {text}{RESET}")
    print(f"{BLUE}{'─' * width}{RESET}")

def section(text):
    print(f"\n{CYAN}{BOLD}▶ {text}{RESET}")

def item(text, color=DIM):
    print(f"  {color}•{RESET} {text}")

def success(text):
    print(f"  {GREEN}✓{RESET} {text}")

def warn(text):
    print(f"  {YELLOW}⚠{RESET}  {text}")

def error(text):
    print(f"  {RED}✗{RESET} {text}")

def gauge(label, value, total=100):
    pct   = int((value / total) * 20)
    bar   = "█" * pct + "░" * (20 - pct)
    color = GREEN if value >= 75 else (YELLOW if value >= 40 else RED)
    print(f"  {DIM}{label:<20}{RESET} {color}{bar}{RESET}  {BOLD}{value}{RESET}/{total}")


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main():
    args = parse_args()

    print(f"\n{BOLD}{BLUE}")
    print("  ⬡  OVERLAND INTELLIGENCE SYSTEM")
    print(f"  {DIM}High Desert Expeditions · Tucson, AZ{RESET}")
    print(f"  {DIM}Know the terrain before you move{RESET}\n")

    # Validate file
    file_path = Path(args.file)
    if not file_path.exists():
        error(f"File not found: {args.file}")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Config
    # -----------------------------------------------------------------------
    header("CONFIGURATION")
    item(f"File:     {file_path.name}")
    item(f"LLM:      {args.llm}")
    item(f"Search:   {args.search}")
    item(f"Question: {args.question[:80]}{'...' if len(args.question) > 80 else ''}")

    # -----------------------------------------------------------------------
    # Load providers
    # -----------------------------------------------------------------------
    section("Loading providers")
    try:
        from config.llm_factory import get_llm
        from config.embedding_factory import get_embeddings
        llm        = get_llm(args.llm)
        embeddings = get_embeddings()
        success("LLM and embeddings ready")
    except Exception as e:
        error(f"Provider error: {e}")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Profile data
    # -----------------------------------------------------------------------
    section("Profiling data")
    try:
        from tools.data_tools import load_dataframe, clean_dataframe, profile_dataframe
        df      = clean_dataframe(load_dataframe(str(file_path)))
        profile = profile_dataframe(df)
        success(f"{profile['shape']['rows']:,} rows × {profile['shape']['columns']} columns")
        success(f"Data health score: {profile.get('data_health_score', 0)}/100")
    except Exception as e:
        error(f"Data load failed: {e}")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Suggested questions
    # -----------------------------------------------------------------------
    section("Generating suggested questions")
    try:
        from agents.question_suggester import generate_suggested_questions
        suggestions = generate_suggested_questions(str(file_path), llm)
        for i, q in enumerate(suggestions, 1):
            item(f"{i}. {q}", CYAN)
    except Exception as e:
        warn(f"Suggester skipped: {e}")

    # -----------------------------------------------------------------------
    # Run pipeline
    # -----------------------------------------------------------------------
    header("RUNNING PIPELINE")
    print(f"\n  {DIM}Question:{RESET} {args.question}\n")

    node_labels = {
        "ingest_rag":   "RAG Ingest",
        "data_analyst": "Data Analyst",
        "research":     "Market Research",
        "insights":     "Insights Engine",
    }

    # Instrument nodes to print progress
    from graph import workflow as wf
    original_factories = {
        "ingest_rag":   wf._make_ingest_node,
        "data_analyst": wf._make_data_analyst_node,
        "research":     wf._make_research_node,
        "insights":     wf._make_insights_node,
    }

    def make_instrumented(node_id, factory, *factory_args):
        node = factory(*factory_args)
        def wrapped(state):
            label = node_labels.get(node_id, node_id)
            print(f"  {YELLOW}◎{RESET} {label:<22} {DIM}running...{RESET}", end="\r", flush=True)
            t0     = time.time()
            result = node(state)
            elapsed = round(time.time() - t0, 1)
            status  = result.get("status", "")
            color   = RED if "failed" in status else GREEN
            symbol  = "✗" if "failed" in status else "✓"
            print(f"  {color}{symbol}{RESET} {label:<22} {DIM}{elapsed}s{RESET}          ")
            return result
        return wrapped

    from langgraph.graph import StateGraph, END
    from graph.workflow import BIAgentState

    graph = StateGraph(BIAgentState)
    graph.add_node("ingest_rag",   make_instrumented("ingest_rag",   wf._make_ingest_node,      embeddings))
    graph.add_node("data_analyst", make_instrumented("data_analyst", wf._make_data_analyst_node, llm))
    graph.add_node("research",     make_instrumented("research",     wf._make_research_node,     llm, args.search))
    graph.add_node("insights",     make_instrumented("insights",     wf._make_insights_node,     llm))
    graph.set_entry_point("ingest_rag")
    graph.add_edge("ingest_rag",   "data_analyst")
    graph.add_edge("data_analyst", "research")
    graph.add_edge("research",     "insights")
    graph.add_edge("insights",     END)
    pipeline = graph.compile()

    initial_state = {
        "uploaded_file_path":  str(file_path),
        "business_question":   args.question,
        "supporting_docs":     [],
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

    pipeline_start = time.time()
    try:
        state = pipeline.invoke(initial_state)
    except Exception as e:
        error(f"Pipeline failed: {e}")
        sys.exit(1)

    # Report agent
    print(f"  {YELLOW}◎{RESET} {'Report Writer':<22} {DIM}running...{RESET}", end="\r", flush=True)
    t0 = time.time()
    try:
        from agents.report_agent import run_report_agent
        state = run_report_agent(dict(state), llm)
        print(f"  {GREEN}✓{RESET} {'Report Writer':<22} {DIM}{round(time.time()-t0, 1)}s{RESET}          ")
    except Exception as e:
        print(f"  {RED}✗{RESET} {'Report Writer':<22} {DIM}failed{RESET}          ")
        warn(str(e))

    total_elapsed = round(time.time() - pipeline_start, 1)

    # -----------------------------------------------------------------------
    # Results
    # -----------------------------------------------------------------------
    header("RESULTS")

    section("Instruments")
    gauge("Data Health",   state.get("data_health_score", 0))
    gauge("Confidence",    state.get("confidence_score",  0))
    gauge("Market Signal", min(100, len(state.get("market_findings", [])) * 15))

    section("Data Findings")
    for finding in state.get("data_findings", [])[:6]:
        item(finding)

    section("Market Intelligence")
    for finding in state.get("market_findings", [])[:4]:
        item(finding)

    section("Strategic Recommendations")
    for rec in state.get("recommendations", []):
        priority = rec.get("priority", "medium").upper()
        color    = RED if priority == "HIGH" else (PURPLE if priority == "MEDIUM" else DIM)
        print(f"\n  {BOLD}#{rec.get('rank','?')} {rec.get('action','')}{RESET}")
        print(f"  {DIM}{rec.get('rationale','')}{RESET}")
        print(f"  {color}● {priority}{RESET}  {DIM}⧖ {rec.get('timeframe','').replace('_',' ').upper()}{RESET}")

    section("Executive Summary")
    summary = state.get("executive_summary", "")
    if summary:
        # Word-wrap at 66 chars
        words, line = summary.split(), ""
        for word in words:
            if len(line) + len(word) + 1 > 66:
                print(f"  {DIM}{line}{RESET}")
                line = word
            else:
                line = (line + " " + word).strip()
        if line:
            print(f"  {DIM}{line}{RESET}")

    # -----------------------------------------------------------------------
    # PDF
    # -----------------------------------------------------------------------
    if not args.no_pdf and state.get("report_markdown"):
        section("Generating PDF report")
        try:
            from tools.chart_tools import generate_all_charts
            from output.pdf_builder import build_pdf
            charts   = generate_all_charts(df)
            pdf_path = build_pdf(state["report_markdown"], charts)
            success(f"Report saved: {pdf_path}")
        except Exception as e:
            warn(f"PDF generation failed: {e}")

    # -----------------------------------------------------------------------
    # Errors
    # -----------------------------------------------------------------------
    errors = state.get("errors", [])
    if errors:
        section("Pipeline warnings")
        for err in errors:
            warn(err)

    # -----------------------------------------------------------------------
    # Footer
    # -----------------------------------------------------------------------
    header(f"COMPLETE  —  {total_elapsed}s total")
    print(f"\n  {DIM}To run the full interactive dashboard:{RESET}")
    print(f"  {CYAN}uvicorn app_api:app --reload --port 8000{RESET}")
    print(f"  {DIM}Then open app.html in your browser.{RESET}\n")


if __name__ == "__main__":
    main()