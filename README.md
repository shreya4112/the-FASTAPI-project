# the-FASTAPI-project
Tredence company Project - SHREYA AGRAWAL ( AI BACKEND)


PROJECT LAYOUT
ai-backend-assignment/
├─ app/
│  ├─ __init__.py
│  ├─ main.py
│  ├─ graph_engine.py
│  ├─ tools.py
│  ├─ workflows.py
│  └─ schemas.py
├─ README.md
└─ requirements.txt


# Minimal Workflow / Agent Engine (AI Engineering Assignment)

This repository implements a small workflow/graph engine and a sample Code Review mini-agent using FastAPI.

# What this project contains

- A minimal graph engine (nodes, edges, branching, loop support).
- A simple tool registry (`app/tools.py`) of pure Python functions used as node actions.
- Sample workflow (Option A: Code Review Mini-Agent) with `extract`, `check_complexity`, `detect_issues`, `suggest_improvements`, `compute_quality`.
- FastAPI endpoints:
  - `POST /graph/create` - create a graph from JSON (returns `graph_id`).
  - `POST /graph/create_sample_code_review` - convenience endpoint to create a ready-to-run sample Code Review graph.
  - `POST /graph/run` - run a graph. Query param `?background=true` runs asynchronously and returns a `run_id`.
  - `GET /graph/state/{run_id}` - get current state and execution log for a run.
  - `GET /health` - health check.

## How to run

1. Create a virtual environment (recommended) and install deps:

## bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
 important : Use the OpenAPI docs at http://127.0.0.1:8000/docs to test endpoints.
## server
uvicorn app.main:app --reload

## Create the sample graph:
POST /graph/create_sample_code_review?threshold=70
Response:
{"graph_id": "..." }

## run the graph synchronized
POST /graph/run
Body:
{
  "graph_id": "<graph_id>",
  "initial_state": {
    "code": "def foo():\\n    pass\\n# TODO: improve\\n"
  }
}

## or run the bg:
POST /graph/run?background=true
Body same as above.

## response return the run id 
GET /graph/state/{run_id}

