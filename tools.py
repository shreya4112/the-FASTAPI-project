"""
Tool registry: register small pure-Python functions that operate on state.
Nodes call these tools.
"""

from typing import Dict, Any, Tuple
import asyncio

TOOLS = {}

def register(name):
    def deco(fn):
        TOOLS[name] = fn
        return fn
    return deco

@register("extract_functions")
async def extract_functions(state: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dummy extraction: given state['code'] (string), split by 'def ' occurrences.
    Produces functions list and set a base 'quality_score' start.
    """
    await asyncio.sleep(0)  # keep it async-friendly
    code = state.get("code", "")
    funcs = []
    for part in code.split("def "):
        part = part.strip()
        if not part:
            continue
        first_line = part.splitlines()[0]
        name = first_line.split("(")[0].strip()
        funcs.append(name)
    return {"functions": funcs, "quality_score": state.get("quality_score", 0)}

@register("check_complexity")
async def check_complexity(state: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple complexity heuristic: longer function names or long code => higher complexity.
    """
    await asyncio.sleep(0)
    code = state.get("code", "")
    lines = code.splitlines()
    complexity = max(1, len(lines) // 10)  # very naive
    return {"complexity": complexity}

@register("detect_issues")
async def detect_issues(state: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple rule-based issue detection:
      - long lines > 120 chars => issue
      - TODO comments => issue
    """
    await asyncio.sleep(0)
    code = state.get("code", "")
    issues = []
    lines = code.splitlines()
    for i, ln in enumerate(lines, start=1):
        if len(ln) > 120:
            issues.append({"line": i, "type": "long_line"})
        if "TODO" in ln or "FIXME" in ln:
            issues.append({"line": i, "type": "todo"})
    return {"issues": issues, "num_issues": len(issues)}

@register("suggest_improvements")
async def suggest_improvements(state: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Suggest some simple, deterministic improvements (strings). Also increment quality score.
    """
    await asyncio.sleep(0)
    suggestions = []
    if state.get("complexity", 0) > 3:
        suggestions.append("Consider splitting large functions into smaller ones.")
    if state.get("num_issues", 0) > 0:
        suggestions.append("Address TODOs and long lines; add tests.")
    if not suggestions:
        suggestions.append("Code style looks OK. Consider adding docstrings.")
    # improve quality score slightly
    qs = state.get("quality_score", 0) + max(1, 5 - state.get("num_issues", 0))
    return {"suggestions": suggestions, "quality_score": qs}

@register("compute_quality")
async def compute_quality(state: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute a simple quality score based on issues and complexity.
    """
    await asyncio.sleep(0)
    base = 50
    penalties = state.get("complexity", 0) * 5 + state.get("num_issues", 0) * 8
    quality = max(0, base - penalties + state.get("quality_score", 0))
    return {"quality_score": quality}
