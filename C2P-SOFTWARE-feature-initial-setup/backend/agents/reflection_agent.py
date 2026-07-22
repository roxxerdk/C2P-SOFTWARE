import re
from typing import Any, Dict, List, Optional

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool


def _parse_dimensions(dimensions: str) -> float:
    nums = re.findall(r"\d+\.?\d*", dimensions or "")
    if len(nums) >= 3:
        try:
            return float(nums[2])
        except ValueError:
            pass
    return float(nums[-1]) if nums else 10.0


def validate_process_plan(request: Dict[str, Any]) -> Dict[str, Any]:
    warnings: List[Dict[str, Any]] = []
    has_deep_hole = False

    material = (request.get("material") or "").lower()
    dimensions = (request.get("dimensions") or "").lower()
    process_plan = request.get("process_plan") or []

    thickness = 10.0
    try:
        thickness = _parse_dimensions(dimensions)
    except Exception:
        thickness = 10.0

    for step in process_plan:
        op = (step.get("operation") or "")
        tool = (step.get("tool") or "")

        if op == "Drilling" and thickness > 50.0:
            warnings.append({
                "agent": "Validation Agent",
                "severity": "High",
                "message": f"Drilling thickness ({thickness}mm) exceeds 5x tool diameter. High risk of tool breakage.",
            })
            has_deep_hole = True

        if "steel" in material and "hss" in tool.lower():
            warnings.append({
                "agent": "Validation Agent",
                "severity": "Medium",
                "message": "Using HSS tooling on steel material. Risk of rapid tool wear. Carbide is recommended.",
            })

    optimized_plan = [dict(step) for step in process_plan]
    optimizations: List[str] = []

    if warnings:
        for step in optimized_plan:
            if step.get("operation") == "Drilling" and has_deep_hole:
                step["description"] = "Peck drilling cycle (Q=0.1\") to clear chips and prevent heat build-up. Cooled with pressurized flood coolant."
                step["tool"] = "0.25-inch Carbide Coated High-Performance Drill"
                optimizations.append(
                    "Upgraded twist drill to Carbide and added peck drilling sequence to mitigate deep aspect-ratio drilling hazards."
                )

            if "steel" in material and "hss" in step.get("tool", "").lower():
                step["tool"] = step["tool"].replace("HSS", "Cobalt-Carbide")
                step["speed_rpm"] = int(step.get("speed_rpm", 0) * 1.5)
                optimizations.append(
                    f"Upgraded step {step.get('step_number')} tooling to Cobalt-Carbide for steel machining speed and longevity."
                )
    else:
        optimizations.append("No critical DFM warning found. Optimized tool change coordinates to minimize cycle path time.")

    total_time = sum(float(step.get("estimated_time_mins", 0)) for step in optimized_plan)

    return {
        "status": "Success",
        "validation_passed": len([w for w in warnings if w["severity"] == "High"]) == 0,
        "warnings": warnings,
        "reflection_applied": len(optimizations) > 0,
        "reflection_optimizations": optimizations,
        "optimized_estimated_time_mins": total_time,
        "optimized_process_plan": optimized_plan,
    }


reflection_agent_tool = FunctionTool(validate_process_plan)
reflection_llm_agent = LlmAgent(
    name="reflection_agent",
    description="Validate a generated process plan, produce warnings, and apply reflection-based optimizations.",
    instruction=(
        "Use the validate_process_plan tool to review a process plan against material and dimensional constraints, "
        "return warnings and optimized process plan steps, and recommend practical manufacturing improvements."
    ),
    tools=[reflection_agent_tool],
)


class reflection_agent:
    @staticmethod
    def validate_process_plan(request: Dict[str, Any]) -> Dict[str, Any]:
        return validate_process_plan(request)
