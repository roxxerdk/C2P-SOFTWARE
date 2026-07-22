from typing import Dict, Any, List

from .perception_agent import perception_agent, perception_llm_agent
from .ballooning_agent import ballooning_agent, ballooning_llm_agent
from .memory_agent import memory_agent, memory_llm_agent
from .expert_agent import expert_agent, expert_llm_agent
from .reflection_agent import reflection_agent, reflection_llm_agent
from .documentation_agent import documentation_agent, documentation_llm_agent
from google.adk.agents import SequentialAgent


def run_full_pipeline(image_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Run the structured agent pipeline from perception through document generation."""
    
    print("\n" + "="*50)
    print(f"🚀 Starting C2P Multi-Agent Pipeline for: {filename}")
    print("="*50)

    # 1. Perception Step
    print("\n[Step 1/5] 🔍 Running Perception Agent...")
    perception_output = perception_agent.analyze_drawing_image(image_bytes, filename)
    print("  └─ Perception complete!")

    # 2. Ballooning Step
    print("[Step 2/5] 🎈 Running Ballooning Agent...")
    ballooned_output = ballooning_agent.assign_balloons(perception_output)
    print("  └─ Ballooning complete!")

    # 3. RAG Memory Lookup
    print("[Step 3/5] 🧠 Querying RAG Engineering Memory...")
    search_query = f"Process planning guidance for {ballooned_output.get('material')} {ballooned_output.get('category')} components"
    memory_context = memory_agent.search_engineering_memory(
        search_query, collections=["materials", "tools", "process_templates"]
    )
    print("  └─ Memory retrieval complete!")

    # 4. Expert Process Planning Step
    print("[Step 4/5] ⚙️ Running Expert Planning Agent...")
    expert_output = expert_agent.generate_process_plan(ballooned_output, memory_context)
    print("  └─ Expert plan generated!")

    # 5. Reflection & DFM Validation Step
    print("[Step 5/5] 🛡️ Running Reflection & Validation Agent...")
    reflection_request = {
        "category": ballooned_output.get("category", "Unknown"),
        "material": ballooned_output.get("material", "Unknown"),
        "dimensions": ballooned_output.get("dimensions", ""),
        "process_plan": expert_output.get("process_plan", []),
    }
    reflection_output = reflection_agent.validate_process_plan(reflection_request)
    print("  └─ Validation & self-correction complete!")

    # 6. Documentation Generation Step
    print("\n[Finalizing] 📄 Generating Final Manufacturing Report Package...")
    documentation_request = {
        "drawing_name": filename.split(".")[0].replace("_", " ").title(),
        "category": ballooned_output.get("category", "Unknown"),
        "material": ballooned_output.get("material", "Unknown"),
        "dimensions": ballooned_output.get("dimensions", ""),
        "process_plan": reflection_output.get(
            "optimized_process_plan", expert_output.get("process_plan", [])
        ),
        "warnings": reflection_output.get("warnings", []),
        "optimizations": reflection_output.get("reflection_optimizations", []),
    }
    documentation_output = documentation_agent.generate_report(documentation_request)
    print("  └─ Report generated successfully!")

    print("\n" + "="*50)
    print("✅ Pipeline execution finished successfully!")
    print("="*50 + "\n")

    return {
        "perception": perception_output,
        "ballooning": ballooned_output,
        "memory_context": memory_context,
        "plan": expert_output,
        "validation": reflection_output,
        "report": documentation_output,
    }


pipeline_agent = SequentialAgent(
    name="c2p_pipeline",
    description="Sequential pipeline agent orchestrating perception, ballooning, memory retrieval, expert planning, reflection, and documentation.",
    sub_agents=[
        perception_llm_agent,
        ballooning_llm_agent,
        memory_llm_agent,
        expert_llm_agent,
        reflection_llm_agent,
        documentation_llm_agent,
    ],
)