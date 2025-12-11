"""
Pre-built sample workflows. This module defines a Code Review mini-agent graph that uses tools.
We also provide a helper to build a graph definition ready to be created via /graph/create.
"""

from typing import Dict, Any, List
from .graph_engine import new_graph_id

def build_code_review_graph(threshold: int = 70) -> Dict[str, Any]:
    """
    Build a graph matching Option A: Extract -> Check complexity -> Detect issues -> Suggest -> Compute quality -> loop until quality >= threshold
    """
    graph_id = new_graph_id()
    nodes = [
        {"name": "extract", "func": "extract_functions", "params": {}},
        {"name": "complexity", "func": "check_complexity", "params": {}},
        {"name": "detect", "func": "detect_issues", "params": {}},
        {"name": "suggest", "func": "suggest_improvements", "params": {}},
        {"name": "quality", "func": "compute_quality", "params": {"threshold": threshold}},
    ]
    # edges: support branching after quality node: if quality >= threshold -> end (no next), else go to suggest or loop
    edges = {
        "extract": "complexity",
        "complexity": "detect",
        "detect": "suggest",
        "suggest": "quality",
        "quality": [
            # if quality >= threshold -> stop (no next, represent by not including next)
            {"cond": {"key": "quality_score", "op": "ge", "value": threshold}, "next": None},
            {"cond": None, "next": "suggest"}  # otherwise loop to suggestions / improvements
        ],
    }
    # build nodes_map for quick lookup by engine
    nodes_map = {n["name"]: n for n in nodes}
    return {"graph_id": graph_id, "nodes": nodes, "nodes_map": nodes_map, "edges": edges, "start_node": "extract"}
