import json
import re
from typing import Any, Dict, List, Optional, Tuple

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool


def _parse_memory_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(entry, dict):
        return {}

    payload = entry.get("payload")
    if isinstance(payload, dict) and payload:
        return payload

    content = entry.get("content")
    if isinstance(content, str):
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return {}


def _find_material_profile(material: str, memory_context: List[Dict[str, Any]]) -> Dict[str, Any]:
    lower_material = material.lower() if isinstance(material, str) else ""

    for entry in memory_context:
        parsed = _parse_memory_entry(entry)
        if parsed.get("material_name") and lower_material in parsed.get("material_name", "").lower():
            return parsed

    for entry in memory_context:
        parsed = _parse_memory_entry(entry)
        if parsed.get("machining_parameters"):
            return parsed

    return {}


def _gather_tool_candidates(memory_context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for entry in memory_context:
        parsed = _parse_memory_entry(entry)
        tool_type = parsed.get("tool_type") or parsed.get("type")
        configs = parsed.get("configurations")
        if isinstance(configs, list) and configs:
            for cfg in configs:
                candidates.append({
                    "tool_type": tool_type or cfg.get("tool_type") or "Unknown Tool",
                    "diameter_inch": cfg.get("diameter_inch"),
                    "flute_count": cfg.get("flute_count"),
                    "material": cfg.get("material"),
                    "coating": cfg.get("coating"),
                    "recommended_operations": [op.lower() for op in (cfg.get("recommended_operations") or [])],
                    "meta": cfg,
                })
        elif tool_type:
            candidates.append({
                "tool_type": tool_type,
                "diameter_inch": parsed.get("diameter_inch"),
                "flute_count": parsed.get("flute_count"),
                "material": parsed.get("material"),
                "coating": parsed.get("coating"),
                "recommended_operations": [op.lower() for op in (parsed.get("recommended_operations") or [])],
                "meta": parsed,
            })

    return candidates


def _choose_tool(operation: str, candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    op_lower = operation.lower()
    prioritized = []

    if "tap" in op_lower or "thread" in op_lower:
        prioritized = [c for c in candidates if "tap" in (c.get("tool_type") or "").lower() or "thread" in (c.get("tool_type") or "").lower()]
    elif "drill" in op_lower or "hole" in op_lower or "bore" in op_lower:
        prioritized = [c for c in candidates if "drill" in (c.get("tool_type") or "").lower()]
    elif "pocket" in op_lower or "slot" in op_lower:
        prioritized = [c for c in candidates if "endmill" in (c.get("tool_type") or "").lower() and any("pocket" in op for op in c.get("recommended_operations", []))]
    elif "chamfer" in op_lower or "break" in op_lower:
        prioritized = [c for c in candidates if "endmill" in (c.get("tool_type") or "").lower() or "chamfer" in (c.get("tool_type") or "").lower()]
    else:
        prioritized = [c for c in candidates if "endmill" in (c.get("tool_type") or "").lower()]

    if prioritized:
        return prioritized[0]
    return candidates[0] if candidates else None


def _select_machine_type(category: str, memory_context: List[Dict[str, Any]]) -> str:
    category_lower = category.lower() if isinstance(category, str) else ""
    if "shaft" in category_lower:
        return "CNC Lathe with Live Tooling"

    for entry in memory_context:
        parsed = _parse_memory_entry(entry)
        tool_type = (parsed.get("tool_type") or "").lower()
        if "lathe" in tool_type or "turning" in tool_type:
            return "CNC Lathe with Live Tooling"

    return "3-Axis CNC Vertical Mill"


def _select_cutting_speed(material_profile: Dict[str, Any], operation: str) -> Optional[float]:
    if not material_profile:
        return None
    machining_parameters = material_profile.get("machining_parameters") or {}
    op_lower = operation.lower()
    if "drill" in op_lower or "hole" in op_lower or "bore" in op_lower:
        return machining_parameters.get("cutting_speed_sfm", {}).get("carbide_drill")
    if "finish" in op_lower or "surface" in op_lower or "chamfer" in op_lower:
        return machining_parameters.get("cutting_speed_sfm", {}).get("carbide_endmill_finish")
    return machining_parameters.get("cutting_speed_sfm", {}).get("carbide_endmill_rough")


def _select_feed_per_tooth(material_profile: Dict[str, Any], operation: str) -> Optional[float]:
    if not material_profile:
        return None
    feed_table = material_profile.get("machining_parameters", {}).get("feed_per_tooth_inch", {})
    op_lower = operation.lower()
    if "drill" in op_lower or "hole" in op_lower or "bore" in op_lower:
        return feed_table.get("drilling")
    if "finish" in op_lower or "surface" in op_lower or "chamfer" in op_lower:
        return feed_table.get("finish_milling") or feed_table.get("rough_milling")
    if "pocket" in op_lower or "slot" in op_lower:
        return feed_table.get("rough_milling")
    return feed_table.get("rough_milling")


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            match = re.search(r"-?\d+\.?\d*", value)
            if match:
                try:
                    return float(match.group(0))
                except ValueError:
                    return None
    return None


def _compute_speed_feed(tool: Dict[str, Any], material_profile: Dict[str, Any], operation: str) -> Tuple[int, int]:
    diameter = _to_float(tool.get("diameter_inch")) or 0.25
    flutes = int(_to_float(tool.get("flute_count")) or 2)

    speed_sfm = _select_cutting_speed(material_profile, operation) or 350
    feed_per_tooth = _select_feed_per_tooth(material_profile, operation) or 0.003

    rpm = int((speed_sfm * 3.82) / diameter) if diameter > 0 else 1000
    feed = int(rpm * feed_per_tooth * flutes)
    return rpm, feed


def _extract_thread_spec(details: str) -> Optional[str]:
    if not details:
        return None
    details_lower = details.lower()
    taps = re.findall(r"\b(?:\d+-)?\d+(?:/\d+)?-\d+\s*un(?:c|f)?(?:-\d+b)?\b", details_lower)
    if taps:
        return taps[0].upper()
    taps = re.findall(r"\bm\d+(?:\.\d+)?x\d+(?:\.\d+)?\b", details_lower)
    if taps:
        return taps[0].upper()
    taps = re.findall(r"\b\d+[-/]\d+[-/]\d+\s*un(?:c|f)?(?:-\d+b)?\b", details_lower)
    if taps:
        return taps[0].upper()
    return None


def _find_tap_tool_candidate(details: str, candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    thread_spec = _extract_thread_spec(details)
    tap_candidates = [c for c in candidates if "tap" in (c.get("tool_type") or "").lower() or "thread" in (c.get("tool_type") or "").lower()]

    if thread_spec:
        for cand in tap_candidates:
            metadata = cand.get("meta") or {}
            config_thread = metadata.get("thread_size") or metadata.get("tool_size") or ""
            if config_thread and thread_spec.lower() in str(config_thread).lower():
                return cand

    return tap_candidates[0] if tap_candidates else None


def _is_drill_tool(tool: Dict[str, Any]) -> bool:
    tool_type = (tool.get("tool_type") or "").lower()
    return "drill" in tool_type or "jobber" in tool_type or "spot" in tool_type


def _resolve_tool_and_timing(operation: str, details: str, machine: str, memory_context: List[Dict[str, Any]]) -> Tuple[str, int, int, float]:
    candidates = _gather_tool_candidates(memory_context)
    tool = None
    op_lower = operation.lower()

    if "tap" in op_lower or "thread" in op_lower:
        tool = _find_tap_tool_candidate(details, candidates)
    else:
        tool = _choose_tool(operation, candidates)

    if tool and ("tap" in op_lower or "thread" in op_lower) and "tap" not in (tool.get("tool_type") or "").lower():
        tool = None
    if tool and ("drill" in op_lower or "hole" in op_lower or "bore" in op_lower) and not _is_drill_tool(tool):
        tool = None

    if tool:
        tool_name = tool["tool_type"]
        rpm, feed = _compute_speed_feed(tool, _find_material_profile("", memory_context), operation)
        estimated_time = 2.5
    else:
        if "hole" in op_lower or "drill" in op_lower or "bore" in op_lower:
            tool_name = "0.25-inch TiN Coated HSS Jobber Drill"
            rpm = 1200
            feed = 9
            estimated_time = 1.5
        elif "tap" in op_lower or "thread" in op_lower:
            thread_spec = _extract_thread_spec(details)
            if thread_spec:
                tool_name = f"{thread_spec} Tap (HSS)"
            else:
                tool_name = "General Tap (HSS)"
            rpm = 600
            feed = 3
            estimated_time = 2.0
        elif "pocket" in op_lower or "slot" in op_lower:
            tool_name = "3/8-inch 3-Flute Carbide Endmill"
            rpm = 2500
            feed = 30
            estimated_time = 5.5
        elif "chamfer" in op_lower or "break" in op_lower:
            tool_name = "0.25-inch 45-degree Chamfer Mill"
            rpm = 3000
            feed = 18
            estimated_time = 1.0
        else:
            tool_name = "0.5-inch 4-Flute Carbide Endmill"
            rpm = 2200
            feed = 26
            estimated_time = 4.0

    return tool_name, rpm, feed, estimated_time


def _guess_operation(feature: Dict[str, Any]) -> str:
    name = (feature.get("name") or "").lower()
    details = (feature.get("details") or "").lower()

    if "tap" in name or "thread" in name or "unc" in details or "un-" in details:
        return "Tapping"
    if "hole" in name or "drill" in name or "bore" in name:
        return "Drilling"
    if "pocket" in name or "slot" in name:
        return "Pocket Milling"
    if "chamfer" in name or "break" in name or "edge" in details:
        return "Chamfering"
    if "surface finish" in name or "finish" in details:
        return "Finishing"
    if "flatness" in name or "perpendicularity" in name or "position" in name or "profile" in name:
        return "Inspection"
    return "Milling"


def _build_operation_step(step_number: int, feature: Dict[str, Any], machine: str, material_profile: Dict[str, Any], memory_context: List[Dict[str, Any]]) -> Dict[str, Any]:
    operation = _guess_operation(feature)
    details = feature.get("details") or ""
    tool_name, rpm, feed, estimated_time = _resolve_tool_and_timing(operation, details, machine, memory_context)

    description = f"{operation} for {feature.get('name', 'feature')} using specified callout: {details}."
    if operation == "Inspection":
        description = f"Inspect {feature.get('name', 'feature')} and verify tolerance: {details}."

    return {
        "step_number": step_number,
        "operation": operation,
        "description": description,
        "machine": machine,
        "tool": tool_name,
        "speed_rpm": rpm,
        "feed_rate_ipm": feed,
        "estimated_time_mins": estimated_time,
        "balloon": feature.get("balloon"),
    }


def generate_process_plan(drawing_data: Dict[str, Any], memory_context: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(drawing_data, dict):
        raise TypeError("drawing_data must be a dict")
    if not isinstance(memory_context, list):
        memory_context = []

    category = drawing_data.get("category", "")
    material = drawing_data.get("material", "")
    features = drawing_data.get("features") or []
    if not isinstance(features, list):
        features = []

    machine = _select_machine_type(category, memory_context)
    material_profile = _find_material_profile(material, memory_context)

    plan_steps: List[Dict[str, Any]] = []
    step_number = 1

    if not features:
        return {
            "machine_type": machine,
            "process_plan": []
        }

    for feature in features:
        plan_steps.append(_build_operation_step(step_number, feature, machine, material_profile, memory_context))
        step_number += 1

    return {
        "machine_type": machine,
        "process_plan": plan_steps,
    }


expert_agent_tool = FunctionTool(generate_process_plan)
expert_llm_agent = LlmAgent(
    name="expert_agent",
    description="Generate a process plan for manufacturing based on drawing features and memory context.",
    instruction=(
        "Use the generate_process_plan tool when given drawing_data and memory_context to return a structured process plan. "
        "Each plan step should include operation, tool, speed, feed, and balloon association."
    ),
    tools=[expert_agent_tool],
)


class expert_agent:
    @staticmethod
    def generate_process_plan(drawing_data: Dict[str, Any], memory_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        return generate_process_plan(drawing_data, memory_context)
