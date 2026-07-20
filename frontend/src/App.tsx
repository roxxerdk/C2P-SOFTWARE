import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  Cpu, 
  FileText, 
  Layers, 
  Code, 
  Eye,
  Clock
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

  // Agent sequence
  const [agents, setAgents] = useState<AgentProgress[]>([
    { name: 'Planning Agent', status: 'idle', message: 'Waiting for drawing upload...' },
    { name: 'Drawing Understanding Agent', status: 'idle', message: 'Waiting for image upload...' },
    { name: 'Memory Agent', status: 'idle', message: 'Waiting for feature coordinates...' },
    { name: 'Process Planning Agent', status: 'idle', message: 'Waiting for engineering JSON...' },
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

    // Auto trigger balloon layer highlight
    setBalloonLayer(true);
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
                        {balloonLayer && selectedDrawing.features.map((f, i) => (
                          <div 
                            key={f.id}
                            style={{ top: `${30 + i * 20}%`, left: `${40 + i * 10}%` }}
                            className="absolute bg-teal-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold shadow-lg animate-bounce"
                            title={f.details}
                          >
                            {f.balloon}
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
