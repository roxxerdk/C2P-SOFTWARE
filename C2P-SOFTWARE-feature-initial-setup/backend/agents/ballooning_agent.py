import re
from typing import Any, Dict, List, Optional, Tuple

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            match = re.search(r"-?\d+\.?\d*", value)
            if match:
                try:
                    return float(match.group(0))
                except ValueError:
                    return None
    return None


def _extract_position(feature: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    position_fields = feature.get("position") or feature.get("coordinates") or feature.get("bbox") or {}

    if isinstance(position_fields, dict):
        y = _to_float(
            position_fields.get("y")
            or position_fields.get("top")
            or position_fields.get("y0")
            or position_fields.get("y1")
        )
        x = _to_float(
            position_fields.get("x")
            or position_fields.get("left")
            or position_fields.get("x0")
            or position_fields.get("x1")
        )
        if y is not None or x is not None:
            return (y if y is not None else 0.0, x if x is not None else 0.0)

    y = _to_float(feature.get("y") or feature.get("top"))
    x = _to_float(feature.get("x") or feature.get("left"))
    if y is not None or x is not None:
        return (y if y is not None else 0.0, x if x is not None else 0.0)

    return None


def _sort_features(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    annotated: List[Tuple[float, float, int, Dict[str, Any]]] = []
    for index, feature in enumerate(features):
        position = _extract_position(feature)
        if position is None:
            position = (float("inf"), float("inf"))
        annotated.append((position[0], position[1], index, feature))

    annotated.sort(key=lambda item: (item[0], item[1], item[2]))
    return [item[3] for item in annotated]


def assign_balloons(drawing_data: Dict[str, Any]) -> Dict[str, Any]:
    """Assign sequential balloon numbers to every feature in drawing_data."""
    if not isinstance(drawing_data, dict):
        raise TypeError("drawing_data must be a dict")

    features = drawing_data.get("features")
    if not isinstance(features, list):
        return dict(drawing_data)

    sorted_features = _sort_features(features)
    numbered_features: List[Dict[str, Any]] = []

    for balloon_number, feature in enumerate(sorted_features, start=1):
        feature_copy = dict(feature)
        if not feature_copy.get("id"):
            feature_copy["id"] = f"feat_{balloon_number}"
        feature_copy["balloon"] = balloon_number
        numbered_features.append(feature_copy)

    updated_data = dict(drawing_data)
    updated_data["features"] = numbered_features
    return updated_data


ballooning_agent_tool = FunctionTool(assign_balloons)
ballooning_llm_agent = LlmAgent(
    name="ballooning_agent",
    description="Assign sequential balloon identifiers to drawing features based on their spatial order.",
    instruction=(
        "Use the assign_balloons tool to number features in drawing_data sequentially, preserving feature ids and returning "
        "drawing_data with balloon numbers assigned."
    ),
    tools=[ballooning_agent_tool],
)


class ballooning_agent:
    @staticmethod
    def assign_balloons(drawing_data: Dict[str, Any]) -> Dict[str, Any]:
        return assign_balloons(drawing_data)
