#!/usr/bin/env python
import os
import sys
import traceback

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

try:
    from agents.memory_agent import search_engineering_memory
    from agents.expert_agent import generate_process_plan

    print("Testing expert_agent process planning with memory enrichment...")

    drawing_data = {
        "category": "Locknut, Impeller",
        "material": "Steel",
        "dimensions": "8.54x8.56x216.8",
        "features": [
            {"id": "feat_1", "name": "Outer Diameter", "details": "3.499-3.500 [88.88-88.90] diameter", "balloon": 1},
            {"id": "feat_2", "name": "Surface Finish", "details": "63 Ra", "balloon": 2},
            {"id": "feat_3", "name": "Datum A", "details": "Flatness .001 [0.02] relative to Datum A", "balloon": 3},
            {"id": "feat_4", "name": "Drilled Hole", "details": "2X .38 [.97] diameter, .25 [.64] depth", "balloon": 4},
            {"id": "feat_5", "name": "Thread", "details": "2-7/8-12 UN-2B", "balloon": 5},
        ],
    }

    query = "steel deep hole drilling"
    memory_results = search_engineering_memory(query, top_k=5)
    print(f"\nMemory search returned {len(memory_results)} results")
    for idx, result in enumerate(memory_results, start=1):
        print(f"  Result {idx}: collection={result.get('source_collection')} score={result.get('score')}")

    plan = generate_process_plan(drawing_data, memory_results)
    steps = plan.get("process_plan", [])
    print(f"\nGenerated process plan with {len(steps)} steps")

    valid_balloons = {feat.get("balloon") for feat in drawing_data["features"]}
    all_valid = True

    for step in steps:
        balloon = step.get("balloon")
        if balloon is None or balloon not in valid_balloons:
            print(f"✗ Invalid step balloon: {balloon} in step {step.get('step_number')}")
            all_valid = False
        print(f"  Step {step.get('step_number')}: {step.get('operation')}")
        print(f"    tool={step.get('tool')} speed_rpm={step.get('speed_rpm')} feed_rate_ipm={step.get('feed_rate_ipm')} balloon={balloon}")
        print(f"    desc={step.get('description')}")

    if not all_valid:
        raise AssertionError("One or more plan steps have invalid balloon references")

    empty_plan = generate_process_plan(drawing_data, [])
    empty_steps = empty_plan.get("process_plan", [])
    if not isinstance(empty_steps, list):
        raise AssertionError("Fallback process plan did not return a list of steps")

    print(f"\nFallback heuristic plan produced {len(empty_steps)} steps")
    for step in empty_steps:
        if step.get("balloon") is None:
            raise AssertionError("Fallback plan step missing balloon field")

    print("\nAll expert_agent tests passed.")
    sys.exit(0)

except Exception as e:
    print(f"✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
