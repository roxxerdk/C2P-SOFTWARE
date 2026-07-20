import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  Cpu, 
  FileText, 
  Layers, 
  Code, 
  Eye,
  Clock,
  Database
} from 'lucide-react';

interface Feature {
  id: string;
  name: string;
  details: string;
  balloon: number;
}

interface Drawing {
  id: string;
  name: string;
  category: string;
  material: string;
  dimensions: string;
  features: Feature[];
}

interface AgentProgress {
  name: string;
  status: 'idle' | 'running' | 'success' | 'failed';
  message: string;
}

export default function App() {
  const [drawings, setDrawings] = useState<Drawing[]>([]);
  const [selectedDrawing, setSelectedDrawing] = useState<Drawing | null>(null);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'viewer' | 'templates'>('dashboard');
  const [logs, setLogs] = useState<string[]>([]);
  const [structuredJson, setStructuredJson] = useState<any>(null);
  const [balloonLayer, setBalloonLayer] = useState(false);
  const [ocrLayer, setOcrLayer] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(-1);
  const [balloons, setBalloons] = useState<any[]>([]);
  const [ragResults, setRagResults] = useState<any[]>([]);
  const [processPlan, setProcessPlan] = useState<any>(null);

  // Agent sequence
  const [agents, setAgents] = useState<AgentProgress[]>([
    { name: 'Planning Agent', status: 'idle', message: 'Waiting for drawing upload...' },
    { name: 'Drawing Understanding Agent', status: 'idle', message: 'Waiting for image upload...' },
    { name: 'Ballooning Agent', status: 'idle', message: 'Waiting for feature coordinates...' },
    { name: 'Memory Agent', status: 'idle', message: 'Waiting for engineering JSON...' },
    { name: 'Process Planning Agent', status: 'idle', message: 'Waiting for RAG retrieval...' },
    { name: 'Validation Agent', status: 'idle', message: 'Waiting for process sequence...' },
    { name: 'Reflection Agent', status: 'idle', message: 'Waiting for validation results...' },
    { name: 'Documentation Agent', status: 'idle', message: 'Waiting for final process plan...' }
  ]);

  // Load sample drawings from backend
  useEffect(() => {
    fetch('http://localhost:8000/drawings')
      .then(res => res.json())
      .then(data => setDrawings(data))
      .catch(err => console.log('Error loading drawings:', err));
  }, []);

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  const handleCatalogSelect = async (drawing: Drawing) => {
    setSelectedDrawing(drawing);
    addLog(`Selected drawing from catalog: ${drawing.name}`);
    await runPipeline(drawing);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    addLog(`Uploading file: ${file.name}`);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      
      const parsedDrawing: Drawing = {
        id: data.planning_agent.classification,
        name: file.name.split('.')[0],
        category: data.planning_agent.classification,
        material: data.drawing_understanding.material,
        dimensions: data.drawing_understanding.dimensions,
        features: data.drawing_understanding.extracted_features
      };

      setSelectedDrawing(parsedDrawing);
      await runPipeline(parsedDrawing);
      console.log('API Preprocessing logs:', data.preprocessing_logs);
    } catch (err) {
      addLog('Error uploading drawing to backend API.');
    } finally {
      setUploading(false);
    }
  };

  const runPipeline = async (drawing: Drawing) => {
    // Reset agent status
    setAgents(prev => prev.map(a => ({ ...a, status: 'idle', message: 'Waiting...' })));
    setLogs([]);
    setCurrentStep(0);

    // Step 1: Planning Agent
    setAgents(prev => {
      const copy = [...prev];
      copy[0].status = 'running';
      copy[0].message = 'Identifying drawing type and layout formatting...';
      return copy;
    });
    addLog('Planning Agent triggered: Classifying component structure...');
    await new Promise(r => setTimeout(r, 1500));
    setAgents(prev => {
      const copy = [...prev];
      copy[0].status = 'success';
      copy[0].message = `Classified as ${drawing.category} component format.`;
      return copy;
    });
    addLog(`Planning Agent complete: Formatted classified as '${drawing.category}'.`);
    setCurrentStep(1);

    // Step 2: Drawing Understanding Agent
    setAgents(prev => {
      const copy = [...prev];
      copy[1].status = 'running';
      copy[1].message = 'Performing OCR & feature location matching...';
      return copy;
    });
    addLog('Drawing Understanding Agent triggered: Extracting material properties and geometric dimensions...');
    await new Promise(r => setTimeout(r, 1500));
    
    const outputJson = {
      material: drawing.material,
      dimensions: drawing.dimensions,
      features: drawing.features.map(f => f.name),
      raw_features: drawing.features
    };
    setStructuredJson(outputJson);
    setOcrLayer(true);

    setAgents(prev => {
      const copy = [...prev];
      copy[1].status = 'success';
      copy[1].message = 'Structured Engineering JSON output generated.';
      return copy;
    });
    addLog('Drawing Understanding complete. Features and title blocks extracted.');
    setCurrentStep(2);

    // Step 3: Ballooning Agent
    setAgents(prev => {
      const copy = [...prev];
      copy[2].status = 'running';
      copy[2].message = 'Generating visual balloon annotations overlay...';
      return copy;
    });
    addLog('Ballooning Agent triggered: Querying feature positions...');
    await new Promise(r => setTimeout(r, 1200));

    try {
      const res = await fetch('http://localhost:8000/balloon', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ features: drawing.features })
      });
      const data = await res.json();
      setBalloons(data.balloons);
      setBalloonLayer(true);
      setAgents(prev => {
        const copy = [...prev];
        copy[2].status = 'success';
        copy[2].message = `Created ${data.balloons.length} visual balloons.`;
        return copy;
      });
      addLog(`Ballooning Agent complete: Generated ${data.balloons.length} visual balloons.`);
    } catch (err) {
      addLog('Error calling Ballooning Agent.');
    }
    setCurrentStep(3);

    // Step 4: Memory Agent (RAG)
    setAgents(prev => {
      const copy = [...prev];
      copy[3].status = 'running';
      copy[3].message = 'Retrieving standards & manufacturing templates from Qdrant...';
      return copy;
    });
    addLog('Memory Agent triggered: Running semantic search queries...');
    await new Promise(r => setTimeout(r, 1200));

    const searchTerms = drawing.features.map(f => f.name).join(' ');
    try {
      const res = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchTerms, limit: 3 })
      });
      const data = await res.json();
      setRagResults(data.results);
      
      setAgents(prev => {
        const copy = [...prev];
        copy[3].status = 'success';
        copy[3].message = `Retrieved ${data.results.length} related documents.`;
        return copy;
      });
      addLog(`Memory Agent complete: Retrieved ${data.results.length} matching guidelines.`);
    } catch (err) {
      addLog('Error querying Memory Agent RAG database.');
    }
    setCurrentStep(4);

    // Step 5: Process Planning Agent
    setAgents(prev => {
      const copy = [...prev];
      copy[4].status = 'running';
      copy[4].message = 'Sequencing operations and calculating machining feedrates...';
      return copy;
    });
    addLog('Process Planning Agent triggered: Structuring machining sequence...');
    await new Promise(r => setTimeout(r, 1200));

    try {
      const res = await fetch('http://localhost:8000/process-plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category: drawing.category,
          material: drawing.material,
          features: drawing.features
        })
      });
      const data = await res.json();
      setProcessPlan(data);
      
      setAgents(prev => {
        const copy = [...prev];
        copy[4].status = 'success';
        copy[4].message = 'Completed process plan routing sheet.';
        return copy;
      });
      addLog(`Process Planning complete. Machine recommended: ${data.machine_type}`);
    } catch (err) {
      addLog('Error calling Process Planning Agent.');
    }
    setCurrentStep(5);
  };

  return (
    <div className="flex h-screen bg-[#0b0f19] text-gray-100 font-sans">
      {/* Sidebar navigation */}
      <div className="w-64 bg-[#111827] border-r border-gray-800 flex flex-col justify-between">
        <div>
          <div className="p-6 flex items-center space-x-3 border-b border-gray-800">
            <Cpu className="w-8 h-8 text-indigo-500 animate-pulse" />
            <span className="font-bold text-lg tracking-wider bg-gradient-to-r from-indigo-400 to-teal-400 bg-clip-text text-transparent">
              C2P AI COPILOT
            </span>
          </div>
          <nav className="p-4 space-y-2">
            <button 
              onClick={() => setActiveTab('dashboard')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm transition-all ${
                activeTab === 'dashboard' ? 'bg-indigo-600/20 text-indigo-400 border-l-4 border-indigo-500' : 'text-gray-400 hover:bg-gray-800'
              }`}
            >
              <Layers className="w-5 h-5" />
              <span>Pipeline Dashboard</span>
            </button>
            <button 
              onClick={() => setActiveTab('viewer')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm transition-all ${
                activeTab === 'viewer' ? 'bg-indigo-600/20 text-indigo-400 border-l-4 border-indigo-500' : 'text-gray-400 hover:bg-gray-800'
              }`}
            >
              <Eye className="w-5 h-5" />
              <span>Drawing Viewer</span>
            </button>
          </nav>
        </div>
        <div className="p-4 border-t border-gray-800 flex items-center space-x-3 text-xs text-gray-500">
          <Clock className="w-4 h-4" />
          <span>Local Time: 12:46 PM</span>
        </div>
      </div>

      {/* Main content frame */}
      <div className="flex-1 overflow-y-auto p-8">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Header info card */}
            <div className="bg-[#111827]/60 border border-gray-800 p-6 rounded-2xl flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold">Drawing Understanding Pipeline</h1>
                <p className="text-gray-400 text-sm mt-1">Upload a drawing to start the Lyzr orchestration workflow & Google ADK agents execution.</p>
              </div>
              <div className="flex items-center space-x-3">
                <label className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-sm font-semibold cursor-pointer flex items-center space-x-2 shadow-lg transition-all">
                  <Upload className="w-4 h-4" />
                  <span>{uploading ? 'Analyzing...' : 'Upload Drawing'}</span>
                  <input type="file" onChange={handleFileUpload} className="hidden" accept="image/*" />
                </label>
              </div>
            </div>

            {/* Catalog select grid */}
            <div className="grid grid-cols-5 gap-4">
              {drawings.slice(0, 5).map(dr => (
                <button
                  key={dr.id}
                  onClick={() => handleCatalogSelect(dr)}
                  className={`p-4 rounded-xl border text-left transition-all ${
                    selectedDrawing?.id === dr.id 
                      ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300' 
                      : 'bg-[#111827]/40 border-gray-800 hover:border-gray-700 text-gray-400'
                  }`}
                >
                  <div className="text-xs font-semibold uppercase text-indigo-400 mb-1">{dr.category}</div>
                  <div className="font-bold text-sm truncate">{dr.name}</div>
                  <div className="text-xs text-gray-500 mt-2">{dr.dimensions} | {dr.material}</div>
                </button>
              ))}
            </div>

            {/* Split layout: Canvas/Visuals & Logs/Agent Status */}
            <div className="grid grid-cols-12 gap-6">
              {/* Left Column: Visual Canvas & JSON */}
              <div className="col-span-7 space-y-6">
                {/* Visualizer Area */}
                <div className="bg-[#111827]/60 border border-gray-800 rounded-2xl p-6 relative min-h-[300px] flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-4 border-b border-gray-800/80 pb-3">
                    <span className="font-semibold text-sm flex items-center space-x-2">
                      <Layers className="w-4 h-4 text-indigo-400" />
                      <span>Interactive Drawing Viewer</span>
                    </span>
                    <div className="flex space-x-2 text-xs">
                      <button 
                        onClick={() => setOcrLayer(!ocrLayer)}
                        className={`px-3 py-1.5 rounded-lg border transition-all ${ocrLayer ? 'bg-indigo-500/20 border-indigo-400 text-indigo-300' : 'bg-gray-800/40 border-gray-700 text-gray-400'}`}
                      >
                        OCR Layer
                      </button>
                      <button 
                        onClick={() => setBalloonLayer(!balloonLayer)}
                        className={`px-3 py-1.5 rounded-lg border transition-all ${balloonLayer ? 'bg-teal-500/20 border-teal-400 text-teal-300' : 'bg-gray-800/40 border-gray-700 text-gray-400'}`}
                      >
                        Balloons
                      </button>
                    </div>
                  </div>

                  <div className="flex-1 flex items-center justify-center p-8 bg-gray-950/40 border border-gray-800/60 rounded-xl relative overflow-hidden">
                    {selectedDrawing ? (
                      <div className="relative w-full max-w-md h-64 border border-dashed border-gray-800 flex flex-col items-center justify-center bg-gray-900/30 rounded-lg">
                        <div className="text-indigo-400 font-mono text-xs mb-2">CATEGORY: {selectedDrawing.category}</div>
                        <div className="text-lg font-bold mb-4">{selectedDrawing.name}</div>
                        <div className="text-gray-500 text-xs">{selectedDrawing.dimensions} | {selectedDrawing.material}</div>
                        
                        {/* Mock overlay layout */}
                        {ocrLayer && (
                          <div className="absolute inset-0 bg-indigo-500/5 flex flex-col items-start p-4 text-[10px] font-mono text-indigo-400 space-y-1">
                            <div>[OCR: TITLE BLOCK MATCHED]</div>
                            <div>[OCR: MAT={selectedDrawing.material}]</div>
                            <div>[OCR: DIM={selectedDrawing.dimensions}]</div>
                          </div>
                        )}
                        {balloonLayer && balloons.map((b: any) => (
                          <div 
                            key={b.feature_id}
                            style={{ top: `${b.coordinates.y}%`, left: `${b.coordinates.x}%` }}
                            className="absolute bg-teal-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-[10px] font-bold shadow-lg cursor-pointer transform -translate-x-1/2 -translate-y-1/2 hover:scale-125 transition-transform"
                            title={`${b.feature_name}: ${b.details}`}
                          >
                            {b.balloon_number}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-12">
                        <Upload className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                        <p className="text-gray-400 text-sm">No drawing loaded. Upload an image or select a catalog item above.</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Structured JSON display */}
                <div className="bg-[#111827]/60 border border-gray-800 rounded-2xl p-6">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-semibold text-sm flex items-center space-x-2">
                      <Code className="w-4 h-4 text-indigo-400" />
                      <span>Structured Engineering JSON</span>
                    </span>
                  </div>
                  {structuredJson ? (
                    <pre className="bg-gray-950 p-4 rounded-xl text-xs font-mono text-indigo-300 overflow-x-auto border border-gray-800/80">
                      {JSON.stringify(structuredJson, null, 2)}
                    </pre>
                  ) : (
                    <div className="bg-gray-950/40 border border-gray-800/40 p-4 rounded-xl text-center text-xs text-gray-500">
                      Engineering JSON will display here once Drawing Understanding finishes.
                    </div>
                  )}
                </div>

                {/* Memory Agent RAG Retrieval Panel */}
                <div className="bg-[#111827]/60 border border-gray-800 rounded-2xl p-6">
                  <div className="flex items-center justify-between mb-3 border-b border-gray-800/80 pb-3">
                    <span className="font-semibold text-sm flex items-center space-x-2">
                      <Database className="w-4 h-4 text-indigo-400" />
                      <span>Memory Agent RAG Retrieval (Qdrant)</span>
                    </span>
                  </div>
                  {ragResults.length > 0 ? (
                    <div className="space-y-3">
                      {ragResults.map((result: any, idx: number) => (
                        <div key={idx} className="bg-gray-950 p-3 rounded-lg border border-gray-800/80">
                          <div className="flex items-center justify-between text-xs font-bold text-indigo-400 mb-1">
                            <span>{result.title}</span>
                            <span className="bg-indigo-950 text-indigo-300 px-1.5 py-0.5 rounded text-[9px] uppercase">{result.type}</span>
                          </div>
                          <pre className="text-[10px] font-mono text-gray-300 max-h-32 overflow-y-auto whitespace-pre-wrap">
                            {result.content.substring(0, 300)}...
                          </pre>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="bg-gray-950/40 border border-gray-800/40 p-4 rounded-xl text-center text-xs text-gray-500">
                      RAG knowledge base matches will display here once Memory Agent finishes.
                    </div>
                  )}
                </div>

                {/* Process Plan Timeline Panel */}
                <div className="bg-[#111827]/60 border border-gray-800 rounded-2xl p-6">
                  <div className="flex items-center justify-between mb-4 border-b border-gray-800/80 pb-3">
                    <span className="font-semibold text-sm flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-indigo-400" />
                      <span>Recommended Manufacturing Process Plan</span>
                    </span>
                    {processPlan && (
                      <span className="bg-indigo-950 text-indigo-300 border border-indigo-500/20 px-2 py-0.5 rounded text-xs font-bold font-mono">
                        TIME: {processPlan.total_estimated_time_mins} mins
                      </span>
                    )}
                  </div>
                  {processPlan ? (
                    <div className="space-y-6 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-[2px] before:bg-gray-800">
                      {processPlan.process_plan.map((step: any) => (
                        <div key={step.step_number} className="relative pl-8 text-xs">
                          <div className="absolute left-[5px] top-1 bg-indigo-500 border-4 border-gray-950 rounded-full w-2.5 h-2.5 flex items-center justify-center text-white" />
                          <div className="flex justify-between font-bold text-gray-200">
                            <span>Step {step.step_number}: {step.operation}</span>
                            <span className="text-gray-500 font-normal">{step.estimated_time_mins}m</span>
                          </div>
                          <p className="text-gray-400 mt-1">{step.description}</p>
                          <div className="grid grid-cols-2 gap-2 mt-2 bg-gray-950/40 p-2 rounded-lg border border-gray-900/60 font-mono text-[10px] text-indigo-300">
                            <div><strong className="text-gray-500">Tool:</strong> {step.tool}</div>
                            <div><strong className="text-gray-500">Machine:</strong> {step.machine}</div>
                            {step.speed_rpm > 0 && (
                              <>
                                <div><strong className="text-gray-500">Spindle:</strong> {step.speed_rpm} RPM</div>
                                <div><strong className="text-gray-500">Feedrate:</strong> {step.feed_rate_ipm} IPM</div>
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="bg-gray-950/40 border border-gray-800/40 p-4 rounded-xl text-center text-xs text-gray-500">
                      Machining process timeline routing sheet will render here.
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column: Agents Execution status & reasoning logs */}
              <div className="col-span-5 space-y-6">
                {/* Lyzr orchestrator active checklist */}
                <div className="bg-[#111827]/60 border border-gray-800 rounded-2xl p-6">
                  <h2 className="text-sm font-semibold border-b border-gray-800/85 pb-3 mb-4 flex items-center space-x-2">
                    <Cpu className="w-4 h-4 text-indigo-400" />
                    <span>Lyzr Orchestration Active Agents</span>
                  </h2>
                  <div className="space-y-4">
                    {agents.map((agent, i) => (
                      <div key={i} className={`flex items-start justify-between text-xs p-1 rounded-lg transition-all ${i === currentStep ? 'bg-indigo-500/10 border-l-2 border-indigo-400 pl-2' : ''}`}>
                        <div>
                          <div className={`font-semibold ${i === currentStep ? 'text-indigo-300 font-bold' : 'text-gray-300'}`}>{agent.name}</div>
                          <div className="text-gray-500 text-[10px] mt-0.5">{agent.message}</div>
                        </div>
                        <div>
                          {agent.status === 'success' && <span className="bg-teal-500/10 text-teal-400 border border-teal-500/30 px-2 py-0.5 rounded-full font-bold">Complete</span>}
                          {agent.status === 'running' && <span className="bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 px-2 py-0.5 rounded-full font-bold animate-pulse">Running</span>}
                          {agent.status === 'idle' && <span className="bg-gray-800 text-gray-500 px-2 py-0.5 rounded-full">Idle</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Agent Reasoning Stream Logs */}
                <div className="bg-[#111827]/60 border border-gray-800 rounded-2xl p-6">
                  <h2 className="text-sm font-semibold border-b border-gray-800/85 pb-3 mb-3 flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-indigo-400" />
                    <span>Agent Stream reasoning logs</span>
                  </h2>
                  <div className="bg-gray-950 p-4 rounded-xl h-48 overflow-y-auto text-[10px] font-mono text-gray-400 border border-gray-800/80 space-y-1">
                    {logs.length > 0 ? logs.map((log, idx) => (
                      <div key={idx}>{log}</div>
                    )) : (
                      <div className="text-gray-600 italic">Logs are empty. Run pipeline.</div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'viewer' && (
          <div className="bg-[#111827]/60 border border-gray-800 p-8 rounded-2xl space-y-6">
            <h2 className="text-xl font-bold">Drawing Catalog Viewer</h2>
            <div className="grid grid-cols-4 gap-4">
              {drawings.map(dr => (
                <div key={dr.id} className="p-4 bg-gray-900/40 border border-gray-850 rounded-xl space-y-2">
                  <span className="text-[10px] font-bold uppercase text-indigo-400">{dr.category}</span>
                  <h3 className="font-bold text-sm">{dr.name}</h3>
                  <div className="text-xs text-gray-500">Dimensions: {dr.dimensions}</div>
                  <div className="text-xs text-gray-500">Material: {dr.material}</div>
                  <button 
                    onClick={() => { setSelectedDrawing(dr); runPipeline(dr); setActiveTab('dashboard'); }}
                    className="text-xs text-indigo-400 font-semibold hover:underline block pt-2"
                  >
                    Load into Pipeline
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
