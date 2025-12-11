from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

class NodeDef(BaseModel):
    name: str
    func: Optional[str] = None  # name of function to call (from tools or workflows)
    # optional node-specific params
    params: Optional[Dict[str, Any]] = None

class Condition(BaseModel):
    key: str
    op: str  # 'eq', 'neq', 'gt', 'lt', 'ge', 'le'
    value: Any

class EdgeRule(BaseModel):
    cond: Optional[Condition] = None
    next: str

class GraphCreateRequest(BaseModel):
    nodes: List[NodeDef]
    # edges: mapping from node name to either string or list of rules
    edges: Dict[str, Union[str, List[EdgeRule]]]
    start_node: str

class GraphCreateResponse(BaseModel):
    graph_id: str

class RunRequest(BaseModel):
    graph_id: str
    initial_state: Dict[str, Any] = {}
    # optional run options (e.g., threshold overrides)
    options: Optional[Dict[str, Any]] = None

class RunResponse(BaseModel):
    run_id: str
    final_state: Optional[Dict[str, Any]] = None
    log: Optional[List[str]] = None
    status: str

class StateResponse(BaseModel):
    run_id: str
    state: Dict[str, Any]
    status: str
    log: List[str]
