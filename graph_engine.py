"""
Graph engine: runs nodes (callable names) over shared state following edges/rules.
Supports simple branching and loop-until conditions.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from .tools import TOOLS
import inspect

# in-memory stores
GRAPHS: Dict[str, Dict[str, Any]] = {}
RUNS: Dict[str, Dict[str, Any]] = {}

import uuid

def _eval_condition(cond: Dict[str, Any], state: Dict[str, Any]) -> bool:
    if cond is None:
        return True
    key = cond.get("key")
    op = cond.get("op")
    value = cond.get("value")
    v = state.get(key)
    if op == "eq":
        return v == value
    if op == "neq":
        return v != value
    if op == "gt":
        return v is not None and v > value
    if op == "lt":
        return v is not None and v < value
    if op == "ge":
        return v is not None and v >= value
    if op == "le":
        return v is not None and v <= value
    return False

class GraphEngine:
    def __init__(self, graph_def: Dict[str, Any], tools: Dict[str, Callable]):
        """
        graph_def: dict with keys 'nodes' (map name->nodeDef), 'edges', 'start_node'
        tools: mapping name->callable
        """
        self.graph = graph_def
        self.tools = tools

    async def run(self, run_id: str, initial_state: Dict[str, Any], runs_store: Dict[str, Any], stop_on_exception: bool = True, max_steps: int = 1000):
        state = dict(initial_state)
        log: List[str] = []
        runs_store[run_id]["state"] = state
        runs_store[run_id]["status"] = "running"
        runs_store[run_id]["log"] = log

        current = self.graph["start_node"]
        steps = 0

        try:
            while current:
                steps += 1
                if steps > max_steps:
                    log.append(f"Max steps {max_steps} reached; aborting.")
                    break

                # find node definition
                node_def = self.graph["nodes_map"].get(current)
                if node_def is None:
                    log.append(f"Node '{current}' not found. Stopping.")
                    break

                func_name = node_def.get("func")
                params = node_def.get("params", {}) or {}
                log.append(f"Running node '{current}' -> function '{func_name}' with params {params}.")
                # call function from tools or special internal nodes
                result = {}
                if func_name is None:
                    log.append(f"Node '{current}' has no func; skipping.")
                else:
                    fn = self.tools.get(func_name)
                    if fn is None:
                        log.append(f"Function '{func_name}' not found in tools. Skipping.")
                    else:
                        # allow both sync and async functions
                        if inspect.iscoroutinefunction(fn):
                            result = await fn(state, params)
                        else:
                            # run sync function in threadpool
                            loop = asyncio.get_running_loop()
                            result = await loop.run_in_executor(None, lambda: fn(state, params))

                        # merge result into state
                        if isinstance(result, dict):
                            state.update(result)
                        log.append(f"Node '{current}' result keys: {list(result.keys())}")

                runs_store[run_id]["state"] = dict(state)
                runs_store[run_id]["log"] = list(log)

                # determine next node via edges
                edge_spec = self.graph["edges"].get(current)
                next_node = None
                if edge_spec is None:
                    # no outgoing edge -> stop
                    break
                elif isinstance(edge_spec, str):
                    next_node = edge_spec
                elif isinstance(edge_spec, list):
                    # list of rules: apply first matching cond
                    for rule in edge_spec:
                        cond = rule.get("cond")
                        if cond is None:
                            # default rule
                            next_node = rule.get("next")
                            break
                        if _eval_condition(cond, state):
                            next_node = rule.get("next")
                            break
                else:
                    # unexpected format
                    raise ValueError(f"Invalid edge spec for node {current}: {edge_spec}")

                # check for loop-stop detection:
                # we allow an edge that points back to an earlier node; user graph can create loops.
                # The engine will rely on conditions and max_steps to exit.
                if next_node == current:
                    log.append(f"Node '{current}' loops to itself; check condition to avoid infinite loops.")
                if next_node is None:
                    break
                log.append(f"Transition: {current} -> {next_node}")
                current = next_node

                # very small pause to allow state checks externally during long runs
                await asyncio.sleep(0)

            runs_store[run_id]["status"] = "completed"
            runs_store[run_id]["state"] = dict(state)
            runs_store[run_id]["log"] = list(log)
            return {"final_state": state, "log": log}
        except Exception as e:
            runs_store[run_id]["status"] = "failed"
            runs_store[run_id]["error"] = str(e)
            log.append(f"Exception during run: {e}")
            runs_store[run_id]["log"] = list(log)
            if stop_on_exception:
                raise
            return {"final_state": state, "log": log}

# helpers to create graph and run IDs
def new_graph_id() -> str:
    return str(uuid.uuid4())

def new_run_id() -> str:
    return str(uuid.uuid4())
