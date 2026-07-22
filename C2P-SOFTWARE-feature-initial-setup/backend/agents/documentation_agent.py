from io import BytesIO
from typing import Any, Dict, List

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool


def generate_report(request: Dict[str, Any]) -> Dict[str, Any]:
    drawing_name = request.get("drawing_name", "drawing")
    category = request.get("category", "Unknown")
    material = request.get("material", "Unknown")
    dimensions = request.get("dimensions", "Unknown")
    process_plan = request.get("process_plan") or []
    warnings = request.get("warnings") or []
    optimizations = request.get("optimizations") or []

    total_time = sum(float(step.get("estimated_time_mins", 0)) for step in process_plan)

    steps_html = ""
    for step in process_plan:
        speeds_html = (
            f"<td>{step.get('speed_rpm')} RPM</td><td>{step.get('feed_rate_ipm')} IPM</td>"
            if step.get("speed_rpm", 0) > 0
            else "<td>-</td><td>-</td>"
        )
        steps_html += f"""
        <tr>
            <td>{step.get('step_number')}</td>
            <td><strong>{step.get('operation')}</strong></td>
            <td>{step.get('description')}</td>
            <td>{step.get('tool')}</td>
            <td>{step.get('machine')}</td>
            {speeds_html}
            <td>{step.get('estimated_time_mins')} min</td>
        </tr>
        """

    warnings_html = ""
    if warnings:
        for warning in warnings:
            warnings_html += f"<li><strong>[{warning.get('severity')}]</strong> {warning.get('message')}</li>"
    else:
        warnings_html = "<li>No critical DFM warnings reported.</li>"

    optimizations_html = ""
    if optimizations:
        for opt in optimizations:
            optimizations_html += f"<li>{opt}</li>"
    else:
        optimizations_html = "<li>No critical optimizations required.</li>"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset=\"utf-8\">
        <title>Manufacturing Process Package - {drawing_name}</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.5; margin: 40px; }}
            h1, h2 {{ color: #1e3a8a; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 25px; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: left; font-size: 13px; }}
            th {{ background: #f1f5f9; color: #1e3a8a; }}
            tr:nth-child(even) {{ background: #f8fafc; }}
            .metadata {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; background: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 25px; }}
            .metadata div {{ font-size: 13px; }}
            .metadata strong {{ color: #1e3a8a; }}
            .alert-container {{ border-left: 4px solid #f59e0b; background: #fffbeb; padding: 15px; border-radius: 4px; margin-bottom: 20px; }}
            .alert-title {{ font-weight: bold; color: #b45309; margin-bottom: 5px; font-size: 14px; }}
            .opt-container {{ border-left: 4px solid #10b981; background: #ecfdf5; padding: 15px; border-radius: 4px; margin-bottom: 25px; }}
            .opt-title {{ font-weight: bold; color: #047857; margin-bottom: 5px; font-size: 14px; }}
            .footer {{ text-align: center; font-size: 11px; color: #64748b; margin-top: 50px; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <h1>C2P Manufacturing Process Package</h1>
        <div class=\"metadata\">
            <div><strong>Drawing Name:</strong> {drawing_name}</div>
            <div><strong>Format Class:</strong> {category}</div>
            <div><strong>Material:</strong> {material}</div>
            <div><strong>Dimensions:</strong> {dimensions}</div>
        </div>

        <h2>Design Rules Check (DFM Validation)</h2>
        <div class=\"alert-container\">
            <div class=\"alert-title\">DFM Validation Warnings</div>
            <ul>{warnings_html}</ul>
        </div>

        <h2>Self-Correction & Optimizations (Reflection Agent)</h2>
        <div class=\"opt-container\">
            <div class=\"opt-title\">Optimizations Applied</div>
            <ul>{optimizations_html}</ul>
        </div>

        <h2>Operations Sequence & Tooling Sheet</h2>
        <table>
            <thead>
                <tr>
                    <th>Seq</th>
                    <th>Operation</th>
                    <th>Process Description</th>
                    <th>Recommended Tooling</th>
                    <th>Recommended Machine</th>
                    <th>Speed (RPM)</th>
                    <th>Feed (IPM)</th>
                    <th>Est. Time</th>
                </tr>
            </thead>
            <tbody>
                {steps_html}
            </tbody>
        </table>

        <p><strong>Total Estimated Machining Time:</strong> {total_time} minutes</p>

        <div class=\"footer\">
            Generated by C2P AI Copilot Workspace Multi-Agent System. Powered by Google ADK & Live Gemini Multimodal Vision API.
        </div>
    </body>
    </html>
    """

    return {
        "status": "Success",
        "drawing_name": drawing_name,
        "report_html": html_content,
    }


documentation_agent_tool = FunctionTool(generate_report)
documentation_llm_agent = LlmAgent(
    name="documentation_agent",
    description="Generate an HTML report package from validated process plan and reflection outputs.",
    instruction=(
        "Use the generate_report tool to turn drawing metadata, process plan steps, warnings, and optimizations into a polished HTML report."
    ),
    tools=[documentation_agent_tool],
)


class documentation_agent:
    @staticmethod
    def generate_report(request: Dict[str, Any]) -> Dict[str, Any]:
        return generate_report(request)
