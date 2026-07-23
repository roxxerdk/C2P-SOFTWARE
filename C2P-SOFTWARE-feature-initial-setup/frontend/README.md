# C2P Manufacturing Copilot

This project is a full-stack engineering drawing analysis and manufacturing planning assistant. A user uploads a technical drawing, the backend runs a staged multi-agent workflow, and the frontend displays the extracted metadata, process plan, validation warnings, and generated manufacturing report.

## What the app does

The current workflow is built around a sequential pipeline:

1. Perception agent
   - extracts drawing metadata such as category, material, dimensions, and features
2. Ballooning agent
   - assigns feature numbers and prepares the drawing overlay structure
3. Memory agent
   - retrieves relevant manufacturing context from Qdrant / local knowledge memory
4. Expert planning agent
   - generates a machining process plan
5. Reflection / validation agent
   - checks the plan for DFM issues and applies optimizations
6. Documentation agent
   - produces an HTML manufacturing report package

The backend exposes a streaming endpoint for this flow and the frontend consumes it via Server-Sent Events (SSE).

## Project structure

- backend/
  - main.py: FastAPI application and streaming pipeline endpoint
  - agents/: modular agents for perception, ballooning, memory, planning, reflection, and documentation
  - rag_engine.py: semantic search and memory persistence into Qdrant
  - requirements.txt: Python dependencies
- frontend/
  - src/App.tsx: main UI for uploading drawings and displaying the pipeline results
  - src/main.tsx: React entry point
- dataset/
  - drawings, materials, process_templates, standards, tools: sample engineering data
- docker-compose.yml
  - starts a local Qdrant vector database instance

## Tech stack

### Backend
- Python
- FastAPI
- Google ADK
- Google Generative AI
- Qdrant
- Sentence Transformers
- Python multipart / dotenv

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- Lucide icons

## Local setup

### 1. Start Qdrant

From the project root:

```bash
docker compose up -d
```

### 2. Backend setup

```bash
cd backend
pip install -r requirements.txt
```

Create a .env file in the backend folder with at least:

```env
GEMINI_API_KEY=your_api_key_here
QDRANT_URL=http://localhost:6333
```

Run the backend:

```bash
uvicorn main:app --reload --port 8000
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available from the Vite dev server.

## API overview

### Health check
- GET /health

### Drawing catalog
- GET /drawings

### Pipeline execution
- POST /run-pipeline
  - accepts an uploaded drawing file
  - streams stage updates over SSE
  - returns the full processed result at the end

## Notes

- The system is designed to work with local sample datasets and can also enrich results from Qdrant-backed memory.
- The frontend keeps a local history of processed runs in browser storage.
- The generated report is available as an HTML download after processing.

## Development status

The project currently supports:
- drawing upload and preview
- streamed multi-agent execution
- process plan generation
- reflection and validation summaries
- HTML report generation
- memory persistence to Qdrant
