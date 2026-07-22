# C2P Software Project Workflow Summary

## Architecture Overview

- `backend/`: Python FastAPI service.
- `frontend/`: React + Vite UI.
- `dataset/`: Static knowledge and template data for drawings, materials, tools, process templates, and standards.

## High-Level Workflow

1. User uploads a drawing image in the frontend.
2. Frontend sends the image to backend `POST /upload`.
3. Backend attempts image parsing with Google Gemini if `GEMINI_API_KEY` is configured.
4. Parsed results are returned to the frontend, including classification, material, dimensions, and features.
5. Frontend then runs a sequential pipeline of agents:
   - Planning Agent
   - Drawing Understanding Agent
   - Ballooning Agent
   - Memory Agent (RAG search)
   - Process Planning Agent
   - Validation Agent
   - Reflection Agent
   - Documentation Agent
6. Final output includes a structured process plan, warnings, optimizations, and a downloadable report.

## Backend Endpoints

- `GET /`: Root status message.
- `GET /health`: Health check.
- `GET /drawings`: Returns pre-configured catalog drawings.
- `POST /upload`: Accepts the drawing image, triggers Gemini analysis if available, and returns structured drawing data.
- `POST /balloon`: Generates feature balloon coordinates for drawing features.
- `POST /search`: Performs a local semantic search over the dataset knowledge base.
- `POST /process-plan`: Generates machining operations and workflow steps based on the extracted drawing data.
- `POST /validate`: Validates the generated process plan and applies optimizations.
- `POST /download-report`: Generates an HTML manufacturing report package.

## Gemini API Usage

- `backend/main.py` loads `GEMINI_API_KEY` from `.env`.
- If the key exists, `google.generativeai` is configured.
- The `/upload` endpoint uses `genai.GenerativeModel("gemini-3.5-flash")` and sends:
  - a drawing parsing prompt
  - the uploaded image bytes
- The Gemini response is parsed into:
  - `category`
  - `material`
  - `dimensions`
  - `features`
- If Gemini fails or the key is absent, the backend falls back to filename/catalog matching.

## Frontend Pipeline

- Upload UI sends image to backend `/upload`.
- The returned drawing data is stored in `selectedDrawing`.
- `runPipeline()` executes the pseudo-agent workflow.
- It also calls backend endpoints for balloon generation, RAG search, process planning, validation, and report download.

## Local RAG Knowledge Base

`backend/rag_engine.py` loads the following data into a local knowledge base:
- `dataset/standards/*.md`
- `dataset/process_templates/*.json`
- `dataset/tools/*.json`
- `dataset/materials/*.json`

Search is keyword-based and returns the most relevant documents.

## Process Planning Logic

- `POST /process-plan` builds a process plan using heuristics based on:
  - component category
  - material
  - extracted features
- It selects machine type, tools, speeds, feeds, and step descriptions.

## Validation and Reflection

- `POST /validate` inspects plan steps and material choices.
- It raises warnings for issues such as:
  - deep-hole drilling
  - steel machining with HSS tooling
- It can modify the process plan to safer tooling and speeds.

## What Actually Happens

- Uploaded images are analyzed only when Gemini is available and successful.
- The planning pipeline still runs afterward, but if Gemini fails the data comes from fallback logic.
- The process plan itself is locally generated, not by Gemini.

## Notes

- The project is designed as a hybrid system: Gemini for drawing extraction, local heuristics for process planning.
- If you want the backend to always use image content rather than fallback file-name matching, ensure `GEMINI_API_KEY` is valid and `POST /upload` does not fail.
