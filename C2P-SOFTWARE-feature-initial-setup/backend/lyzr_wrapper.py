import os
import json
from typing import Any, Dict, Optional

try:
    import lyzr
except Exception as exc:  # pragma: no cover - import guard for environments without SDK
    lyzr = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


class LyzrPipelineWrapper:
    """Thin compatibility wrapper around the installed Lyzr SDK.

    The project already has a working sequential pipeline implemented in Python.
    This wrapper exposes the same interface as a Lyzr-style agent so the backend
    can optionally route through the SDK when it is installed.
    """

    def __init__(self, runner: Optional[Any] = None, name: str = "c2p_pipeline") -> None:
        self.runner = runner
        self.name = name

    def run(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        if self.runner is None:
            raise RuntimeError("No runner configured for Lyzr pipeline wrapper")
        return self.runner(image_bytes, filename)

    def get_status(self) -> Dict[str, Any]:
        return {"name": self.name, "sdk_available": lyzr is not None, "import_error": str(_IMPORT_ERROR) if _IMPORT_ERROR else None}


def build_lyzr_pipeline_wrapper(runner: Any) -> LyzrPipelineWrapper:
    return LyzrPipelineWrapper(runner=runner)
