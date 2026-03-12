"""
Overland Intelligence System — FastAPI backend
Run with: uvicorn app_api:app --reload --port 8000
"""
import sys
import json
import time
import uuid
import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from config.settings import settings
from config.llm_factory import get_llm
from config.embedding_factory import get_embeddings

app = FastAPI(
    title="Overland Intelligence System",
    version="1.0.0",
    description="High Desert Expeditions — Business Intelligence Pipeline",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory run registry — stores completed results keyed by run_id
# Resets on server restart. Sufficient for local demo use.
_runs: dict[str, dict] = {}


# -----------------------------------------------------------------------------
# Request / Response models
# -----------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    file_id:         str
    business_question: str
    llm_provider:    str = "groq"
    search_provider: str = "duckduckgo"


class UploadResponse(BaseModel):
    file_id:            str
    filename:           str
    rows:               int
    columns:            int
    suggested_questions: list[str]


# -----------------------------------------------------------------------------
# POST /upload
# Accepts a CSV, saves to temp dir, runs question suggester, returns file_id
# -----------------------------------------------------------------------------

@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith((".csv", ".xlsx", ".xls")):
        raise HTTPException(400, "Only CSV and Excel files are supported.")

    # Save to a persistent temp location keyed by a unique id
    file_id = str(uuid.uuid4())
    upload_dir = Path(tempfile.gettempdir()) / "ois_uploads"
    upload_dir.mkdir(exist_ok=True)

    suffix = Path(file.filename).suffix
    dest = upload_dir / f"{file_id}{suffix}"
    content = await file.read()
    dest.write_bytes(content)

    # Profile for row/col count
    from tools.data_tools import load_dataframe, clean_dataframe
    df = clean_dataframe(load_dataframe(str(dest)))
    rows, cols = df.shape

    # Suggested questions — fires lightweight LLM call
    suggested = []
    try:
        llm = get_llm(settings.llm_provider)
        from agents.question_suggester import generate_suggested_questions
        suggested = generate_suggested_questions(df, llm)
    except Exception:
        # Fallback — never block upload on suggester failure
        from agents.question_suggester import _fallback_questions
        from tools.data_tools import profile_dataframe
        suggested = _fallback_questions(profile_dataframe(df))

    # Register file path so /analyze can find it
    _runs[file_id] = {"file_path": str(dest), "filename": file.filename}

    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        rows=rows,
        columns=cols,
        suggested_questions=suggested,
    )


# -----------------------------------------------------------------------------
# POST /analyze/stream
# Runs the full LangGraph pipeline, yields SSE events as each node completes
# -----------------------------------------------------------------------------

@app.post("/analyze/stream")
async def analyze_stream(req: AnalyzeRequest):
    if req.file_id not in _runs:
        raise HTTPException(404, "File not found. Please upload again.")

    file_path = _runs[req.file_id]["file_path"]

    return StreamingResponse(
        _run_pipeline_sse(req, file_path),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


async def _run_pipeline_sse(req: AnalyzeRequest, file_path: str) -> AsyncGenerator[str, None]:
    """
    Runs the pipeline in a thread pool and yields SSE events.

    Event types:
        node_start    — a graph node has started
        node_complete — a graph node has finished
        result        — full pipeline result (final event)
        error         — pipeline failed
    """
    run_id = str(uuid.uuid4())

    def _event(event_type: str, data: dict) -> str:
        payload = json.dumps({"type": event_type, "run_id": run_id, **data})
        return f"data: {payload}\n\n"

    # Emit starting events for each agent so the feed shows them as waiting
    agents = [
        {"id": "ingest_rag",    "name": "RAG Ingest"},
        {"id": "data_analyst",  "name": "Data Analyst"},
        {"id": "research",      "name": "Market Research"},
        {"id": "insights",      "name": "Insights Engine"},
        {"id": "report",        "name": "Report Writer"},
    ]

    for agent in agents:
        yield _event("node_start", {"node": agent["id"], "label": agent["name"]})

    await asyncio.sleep(0.05)

    try:
        llm        = get_llm(req.llm_provider)
        embeddings = get_embeddings()

        # Instrument the graph nodes to emit SSE events as they complete
        # We patch the workflow module's node factories temporarily
        node_events: list[tuple[str, str, float]] = []  # (node_id, status, elapsed)
        start_times: dict[str, float] = {}

        from graph import workflow as wf

        original_factories = {
            "ingest_rag":   wf._make_ingest_node,
            "data_analyst": wf._make_data_analyst_node,
            "research":     wf._make_research_node,
            "insights":     wf._make_insights_node,
        }

        def make_instrumented(node_id, original_factory, *factory_args):
            original_node = original_factory(*factory_args)
            def wrapped(state):
                start_times[node_id] = time.time()
                result = original_node(state)
                elapsed = round(time.time() - start_times[node_id], 1)
                node_events.append((node_id, result.get("status", "complete"), elapsed))
                return result
            return wrapped

        # Build an instrumented graph
        from langgraph.graph import StateGraph, END
        from graph.workflow import BIAgentState

        graph = StateGraph(BIAgentState)
        graph.add_node("ingest_rag",   make_instrumented("ingest_rag",   wf._make_ingest_node,      embeddings))
        graph.add_node("data_analyst", make_instrumented("data_analyst", wf._make_data_analyst_node, llm))
        graph.add_node("research",     make_instrumented("research",     wf._make_research_node,     llm, req.search_provider))
        graph.add_node("insights",     make_instrumented("insights",     wf._make_insights_node,     llm))
        graph.set_entry_point("ingest_rag")
        graph.add_edge("ingest_rag",   "data_analyst")
        graph.add_edge("data_analyst", "research")
        graph.add_edge("research",     "insights")
        graph.add_edge("insights",     END)
        instrumented_graph = graph.compile()

        # Run pipeline in thread so we don't block the event loop
        from concurrent.futures import ThreadPoolExecutor
        import functools

        initial_state = wf.run_pipeline.__wrapped__ if hasattr(wf.run_pipeline, '__wrapped__') else None

        def _run_sync():
            from graph.workflow import BIAgentState
            init = {
                "uploaded_file_path":  file_path,
                "business_question":   req.business_question,
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
            return instrumented_graph.invoke(init)

        loop = asyncio.get_event_loop()
        last_event_count = 0

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = loop.run_in_executor(executor, _run_sync)

            # Poll for node completion events while pipeline runs
            while not future.done():
                await asyncio.sleep(0.3)
                while last_event_count < len(node_events):
                    node_id, status, elapsed = node_events[last_event_count]
                    yield _event("node_complete", {
                        "node":    node_id,
                        "status":  status,
                        "elapsed": f"{elapsed}s",
                    })
                    last_event_count += 1

            # Drain any remaining events
            while last_event_count < len(node_events):
                node_id, status, elapsed = node_events[last_event_count]
                yield _event("node_complete", {
                    "node":    node_id,
                    "status":  status,
                    "elapsed": f"{elapsed}s",
                })
                last_event_count += 1

            pipeline_state = await future

        # Run report agent (not in graph — runs after insights complete)
        yield _event("node_start",    {"node": "report", "label": "Report Writer"})
        report_start = time.time()

        try:
            from agents.report_agent import run_report_agent
            pipeline_state = run_report_agent(dict(pipeline_state), llm)
        except Exception as e:
            msg = getattr(e, "retry_message", None) or str(e)
            pipeline_state["errors"] = pipeline_state.get("errors", []) + [msg]
            pipeline_state["report_markdown"] = ""

        report_elapsed = round(time.time() - report_start, 1)
        yield _event("node_complete", {
            "node":    "report",
            "status":  pipeline_state.get("status", "report_complete"),
            "elapsed": f"{report_elapsed}s",
        })

        # Generate PDF
        pdf_path = ""
        try:
            from tools.data_tools import load_dataframe, clean_dataframe
            from tools.chart_tools import generate_all_charts
            from output.pdf_builder import build_pdf

            df     = clean_dataframe(load_dataframe(file_path))
            charts = generate_all_charts(df)
            pdf_path = build_pdf(pipeline_state.get("report_markdown", ""), charts)
        except Exception as e:
            pipeline_state["errors"] = pipeline_state.get("errors", []) + [f"PDF failed: {str(e)}"]

        # Store completed run for PDF download
        _runs[run_id] = {
            **_runs.get(req.file_id, {}),
            "state":    pipeline_state,
            "pdf_path": pdf_path,
        }

        # Serialize charts for frontend (base64 PNGs)
        charts_payload = {}
        try:
            from tools.data_tools import load_dataframe, clean_dataframe
            from tools.chart_tools import generate_all_charts
            df = clean_dataframe(load_dataframe(file_path))
            charts_payload = generate_all_charts(df)
        except Exception:
            pass

        # Final result event — everything the dashboard needs
        yield _event("result", {
            "run_id":            run_id,
            "data_findings":     pipeline_state.get("data_findings", []),
            "data_summary":      pipeline_state.get("data_summary", ""),
            "data_health_score": pipeline_state.get("data_health_score", 0),
            "market_findings":   pipeline_state.get("market_findings", []),
            "market_summary":    pipeline_state.get("market_summary", ""),
            "recommendations":   pipeline_state.get("recommendations", []),
            "opportunities":     pipeline_state.get("opportunities", []),
            "executive_summary": pipeline_state.get("executive_summary", ""),
            "confidence_score":  pipeline_state.get("confidence_score", 0),
            "report_markdown":   pipeline_state.get("report_markdown", ""),
            "pdf_ready":         bool(pdf_path),
            "errors":            pipeline_state.get("errors", []),
            "charts":            charts_payload,
        })

    except Exception as e:
        retry = getattr(e, "retry_message", None)
        yield _event("error", {
            "message":       str(e),
            "retry_message": retry or "",
        })


# -----------------------------------------------------------------------------
# GET /download/{run_id}
# Serves the generated PDF for the completed run
# -----------------------------------------------------------------------------

@app.get("/download/{run_id}")
async def download_pdf(run_id: str):
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(404, "Run not found.")
    pdf_path = run.get("pdf_path", "")
    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(404, "PDF not available for this run.")
    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename="overland_intelligence_report.pdf",
    )


# -----------------------------------------------------------------------------
# GET /health
# -----------------------------------------------------------------------------

@app.get("/providers")
async def get_providers():
    """
    Returns all registered providers for LLM and search.
    The dashboard uses this to populate dropdowns dynamically —
    adding a new provider to a registry automatically surfaces it in the UI.
    """
    from config.llm_factory import get_available_llm_providers
    from config.search_factory import get_available_search_providers
    return {
        "llm":    get_available_llm_providers(),
        "search": get_available_search_providers(),
    }


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.app_version}