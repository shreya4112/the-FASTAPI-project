from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from .schemas import GraphCreateRequest, GraphCreateResponse, RunRequest, RunResponse, StateResponse
from .graph_engine import GRAPHS, RUNS, GraphEngine, new_graph_id, new_run_id
from .tools import TOOLS
from .workflows import build_code_review_graph
import asyncio

app = FastAPI(title="Minimal Workflow Engine - AI Eng Assignment")

# expose a small health endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/graph/create", response_model=GraphCreateResponse)
async def create_graph(req: GraphCreateRequest):
    # transform incoming nodes list to nodes_map for engine expectations
    graph_id = new_graph_id()
    nodes_map = {n.name: {"name": n.name, "func": n.func, "params": n.params or {}} for n in req.nodes}
    edges = {}
    # normalize edges representation to either string or list
    for key, val in req.edges.items():
        if isinstance(val, str):
            edges[key] = val
        else:
            # Assume list of rules (which may be provided as dicts)
            normalized = []
            for item in val:
                # item expected as dict-like -> ensure has cond dict or None and next
                normalized.append({"cond": item.get("cond"), "next": item.get("next")})
            edges[key] = normalized
    graph_def = {"graph_id": graph_id, "nodes": [n for n in nodes_map.values()], "nodes_map": nodes_map, "edges": edges, "start_node": req.start_node}
    GRAPHS[graph_id] = graph_def
    return {"graph_id": graph_id}

@app.post("/graph/create_sample_code_review", response_model=GraphCreateResponse)
async def create_sample_code_review(threshold: Optional[int] = 70):
    """
    Convenience endpoint to create the sample Code Review graph (Option A).
    """
    graph_def = build_code_review_graph(threshold)
    graph_id = graph_def["graph_id"]
    GRAPHS[graph_id] = graph_def
    return {"graph_id": graph_id}

@app.post("/graph/run", response_model=RunResponse)
async def run_graph(req: RunRequest, background: Optional[bool] = False, background_tasks: BackgroundTasks = None):
    graph_def = GRAPHS.get(req.graph_id)
    if graph_def is None:
        raise HTTPException(status_code=404, detail="Graph not found")
    run_id = new_run_id()
    # prepare run context
    RUNS[run_id] = {"graph_id": req.graph_id, "state": dict(req.initial_state), "status": "pending", "log": []}
    engine = GraphEngine(graph_def, TOOLS)

    async def _run_and_store():
        try:
            await engine.run(run_id, req.initial_state, RUNS)
        except Exception as e:
            # engine.run already marks the run status; catch so background task doesn't crash silently
            RUNS[run_id]["status"] = "failed"
            RUNS[run_id].setdefault("log", []).append(f"Background run exception: {e}")

    if background:
        # Start in background and return run_id immediately
        background_tasks.add_task(_run_and_store)
        return {"run_id": run_id, "status": "running", "final_state": None, "log": []}
    else:
        # run synchronously (await completion) and return final state & log
        await _run_and_store()
        run = RUNS.get(run_id)
        return {"run_id": run_id, "status": run.get("status", "unknown"), "final_state": run.get("state"), "log": run.get("log", [])}

@app.get("/graph/state/{run_id}", response_model=StateResponse)
async def graph_state(run_id: str):
    run = RUNS.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run_id": run_id, "state": run.get("state", {}), "status": run.get("status", "unknown"), "log": run.get("log", [])}
