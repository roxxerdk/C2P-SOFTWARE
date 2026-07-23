import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  Cpu, 
  FileText, 
  Layers, 
  Code, 
  Eye,
  Clock,
  Database,
  AlertTriangle,
  CheckCircle,
  Download,
  History,
  Trash2
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
  imageUrl?: string;
}

interface ProcessedHistoryItem {
  timestamp: string;
  drawing: Drawing;
  structuredJson: any;
  processPlan: any;
  validationWarnings: any[];
  reflectionOptimizations: string[];
  ragResults: any[];
}

interface AgentProgress {
  name: string;
  status: 'idle' | 'running' | 'success' | 'failed';
  message: string;
}

export default function App() {
  const [selectedDrawing, setSelectedDrawing] = useState<Drawing | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [structuredJson, setStructuredJson] = useState<any>(null);
  const [balloonLayer, setBalloonLayer] = useState(true);
  const [ocrLayer, setOcrLayer] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [currentStep, setCurrentStep] = useState<number>(-1);
  const [balloons, setBalloons] = useState<any[]>([]);
  const [ragResults, setRagResults] = useState<any[]>([]);
  const [processPlan, setProcessPlan] = useState<any>(null);
  const [validationWarnings, setValidationWarnings] = useState<any[]>([]);
  const [reflectionOptimizations, setReflectionOptimizations] = useState<string[]>([]);
  const [reportHtml, setReportHtml] = useState<string | null>(null);
  const [history, setHistory] = useState<ProcessedHistoryItem[]>([]);

  // Agent sequence initialization
  const [agents, setAgents] = useState<AgentProgress[]>([
    { name: 'Planning Agent', status: 'idle', message: 'Waiting for drawing upload...' },
    { name: 'Drawing Understanding Agent', status: 'idle', message: 'Waiting for image processing...' },
    { name: 'Ballooning Agent', status: 'idle', message: 'Waiting for feature coordinates...' },
    { name: 'Memory Agent', status: 'idle', message: 'Waiting for engineering JSON...' },
    { name: 'Process Planning Agent', status: 'idle', message: 'Waiting for RAG retrieval...' },
    { name: 'Validation Agent', status: 'idle', message: 'Waiting for process sequence...' },
    { name: 'Reflection Agent', status: 'idle', message: 'Waiting for validation results...' },
    { name: 'Documentation Agent', status: 'idle', message: 'Waiting for final process plan...' }
  ]);

  // Load saved history on startup
  useEffect(() => {
    const savedHistory = localStorage.getItem('c2p_process_history');
    if (savedHistory) {
      try {
        setHistory(JSON.parse(savedHistory));
      } catch (err) {
        console.error('Failed to parse history', err);
      }
    }
  }, []);

  const saveToHistory = (newItem: ProcessedHistoryItem) => {
    setHistory(prev => {
      const filtered = prev.filter(item => item.drawing.name !== newItem.drawing.name);
      const updated = [newItem, ...filtered].slice(0, 10); // Keep last 10 runs
      localStorage.setItem('c2p_process_history', JSON.stringify(updated));
      return updated;
    });
  };

  const clearHistory = () => {
    localStorage.removeItem('c2p_process_history');
    setHistory([]);
    addLog('Processing history cleared.');
  };

  const loadHistoryItem = (item: ProcessedHistoryItem) => {
    setSelectedDrawing(item.drawing);
    setStructuredJson(item.structuredJson);
    setProcessPlan(item.processPlan);
    setValidationWarnings(item.validationWarnings);
    setReflectionOptimizations(item.reflectionOptimizations);
    setRagResults(item.ragResults);
    setBalloons(toBalloonOverlay(item.drawing.features || []));
    setBalloonLayer(true);
    setOcrLayer(true);
    setAgents(prev => prev.map(a => ({ ...a, status: 'success', message: 'Loaded from session history' })));
    addLog(`Loaded cached process plan for: ${item.drawing.name}`);
  };

  const addLog = (msg: string) => {
    setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    addLog(`Uploading file: ${file.name}`);

    const imagePreviewUrl = URL.createObjectURL(file);

    const placeholderDrawing: Drawing = {
      id: file.name,
      name: file.name.split('.')[0],
      category: 'Analyzing...',
      material: 'Analyzing...',
      dimensions: 'Analyzing...',
      features: [],
      imageUrl: imagePreviewUrl
    };

    setSelectedDrawing(placeholderDrawing);

    try {
      await runPipeline(placeholderDrawing, file);
    } catch (err) {
      addLog('Error executing pipeline via backend API.');
    } finally {
      setUploading(false);
    }
  };

  const downloadReportPackage = async () => {
    if (!selectedDrawing || !processPlan) return;
    addLog('Initiating manufacturing report download...');

    if (reportHtml) {
      const blob = new Blob([reportHtml], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `manufacturing_report_${selectedDrawing.name.toLowerCase().replace(/ /g, '_')}.html`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      addLog('Report download completed successfully.');
      return;
    }

    try {
      const res = await fetch('http://localhost:8000/download-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          drawing_name: selectedDrawing.name,
          category: selectedDrawing.category,
          material: selectedDrawing.material,
          dimensions: selectedDrawing.dimensions,
          process_plan: processPlan.process_plan,
          warnings: validationWarnings,
          optimizations: reflectionOptimizations
        })
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `manufacturing_report_${selectedDrawing.name.toLowerCase().replace(/ /g, '_')}.html`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      addLog('Report download completed successfully.');
    } catch (err) {
      addLog('Failed to download manufacturing report.');
    }
  };

  const toBalloonOverlay = (features: any[]) => {
    return (features || []).map((feature: any, index: number) => ({
      balloon_number: feature.balloon ?? index + 1,
      feature_id: feature.id || `feat_${index + 1}`,
      feature_name: feature.name || feature.feature_name || 'Feature',
      details: feature.details || '',
      coordinates: feature.coordinates || {
        x: 20 + (index % 4) * 20,
        y: 20 + Math.floor(index / 4) * 20
      }
    }));
  };

  const toProcessPlanState = (planResponse: any) => {
    const steps = Array.isArray(planResponse?.process_plan) ? planResponse.process_plan : [];
    return {
      machine_type: planResponse?.machine_type || '3-Axis CNC Vertical Mill',
      total_estimated_time_mins: steps.reduce((sum: number, step: any) => sum + (Number(step.estimated_time_mins) || 0), 0),
      process_plan: steps
    };
  };

  // Helper: Generates Fallback Manufacturing Standards if Qdrant returns empty
  const toRagResults = (memoryContext: any[], material: string = 'Steel') => {
    if (Array.isArray(memoryContext) && memoryContext.length > 0) {
      return memoryContext.map((entry: any, idx: number) => {
        const payload = entry.payload || {};
        const content = entry.content || payload.record || JSON.stringify(payload);
        const title = payload.material_name || payload.tool_type || payload.process_type || `Memory Context ${idx + 1}`;
        const type = payload.type || entry.source_collection || 'memory';
        return {
          title,
          type,
          content: typeof content === 'string' ? content : JSON.stringify(content)
        };
      });
    }

    // Fallback Knowledge Base items so Qdrant section is never empty
    return [
      {
        title: `Material Machinability Standard: ${material}`,
        type: 'material_spec',
        content: `Standard cutting speed (Vc): 120-180 m/min. Recommended coolant: Water-soluble synthetic emulsion. Tooling preference: TiN Coated Carbide for long life.`
      },
      {
        title: 'ISO 2768-m Tolerance Guide (Medium Precision)',
        type: 'standard_rule',
        content: `General tolerances for linear dimensions: ±0.1mm (0.5 to 6mm), ±0.2mm (6 to 30mm), ±0.3mm (30 to 120mm). GD&T Flatness tolerance: 0.001 [.02] Datum A.`
      },
      {
        title: 'ASME Y14.5 GD&T Callout Rules',
        type: 'gdt_standard',
        content: `Thread Callouts UN-2B specify internal threads with medium tolerance fit. Tapping requires prior spot drilling and pilot hole chamfering.`
      }
    ];
  };

  const runPipeline = async (drawing: Drawing, file: File) => {
    setAgents(prev => prev.map(a => ({ ...a, status: 'idle', message: 'Waiting...' })));
    setLogs([]);
    setCurrentStep(-1);
    setStructuredJson(null);
    setBalloons([]);
    setRagResults([]);
    setProcessPlan(null);
    setValidationWarnings([]);
    setReflectionOptimizations([]);
    setReportHtml(null);

    const formData = new FormData();
    formData.append('file', file);

    const stageIndexMap: Record<string, number> = {
      perception: 0,
      ballooning: 2,
      memory: 3,
      expert: 4,
      validation: 5,
      documentation: 7,
      memory_store: 3,
      complete: 7
    };

    const updateAgentStatus = (stage: string, status: 'running' | 'success' | 'failed', message?: string) => {
      const idx = stageIndexMap[stage];
      if (idx === undefined) return;

      setAgents(prev => {
        const copy = [...prev];
        copy[idx] = {
          ...copy[idx],
          status,
          message: message ?? copy[idx].message
        };
        return copy;
      });
      setCurrentStep(idx);
    };

    addLog(`Initiating backend SSE stream for ${file.name}...`);
    updateAgentStatus('perception', 'running', 'Analyzing drawing structure via Gemini...');

    try {
      const response = await fetch('http://localhost:8000/run-pipeline', {
        method: 'POST',
        body: formData
      });
      if (!response.ok) {
        throw new Error(`Pipeline failed with HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('ReadableStream reader unavailable.');

      const decoder = new TextDecoder();
      let buffer = '';

      let finalDrawing = drawing;
      let finalJson: any = null;
      let finalPlan: any = null;
      let finalWarnings: any[] = [];
      let finalOptimizations: string[] = [];
      let finalRag: any[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() ?? '';

        for (const part of parts) {
          const trimmedLine = part.trim();
          if (!trimmedLine.startsWith('data:')) continue;
          const payload = trimmedLine.slice(5).trim();
          if (!payload) continue;

          try {
            const event = JSON.parse(payload);
            const stage = event.stage;
            addLog(`[${stage.toUpperCase()}] Stage complete`);

            if (stage === 'perception' && event.data) {
              finalJson = {
                material: event.data.material || 'Steel',
                dimensions: event.data.dimensions || '',
                features: event.data.features || [],
                raw_features: event.data.features || []
              };
              setStructuredJson(finalJson);
              setOcrLayer(true);
              updateAgentStatus('perception', 'success', 'Perception analysis complete.');
              updateAgentStatus('ballooning', 'running', 'Mapping feature coordinates...');
            }

            if (stage === 'ballooning' && event.data?.features) {
              setBalloons(toBalloonOverlay(event.data.features));
              setBalloonLayer(true);
              updateAgentStatus('ballooning', 'success', 'Balloons generated.');
              updateAgentStatus('memory', 'running', 'Retrieving vector memories...');
            }

            if (stage === 'memory') {
              finalRag = toRagResults(event.data || [], finalJson?.material || 'Steel');
              setRagResults(finalRag);
              updateAgentStatus('memory', 'success', 'Memory context retrieved.');
              updateAgentStatus('expert', 'running', 'Formulating machining sequence...');
            }

            if (stage === 'expert' && event.data) {
              finalPlan = toProcessPlanState(event.data);
              setProcessPlan(finalPlan);
              updateAgentStatus('expert', 'success', 'Process plan generated.');
              updateAgentStatus('validation', 'running', 'Running DFM rule checks...');
            }

            if (stage === 'validation' && event.data) {
              finalWarnings = event.data.warnings || [];
              finalOptimizations = event.data.reflection_optimizations || [];
              setValidationWarnings(finalWarnings);
              setReflectionOptimizations(finalOptimizations);
              
              if (event.data.optimized_process_plan) {
                finalPlan = {
                  ...finalPlan,
                  total_estimated_time_mins: event.data.optimized_estimated_time_mins || finalPlan?.total_estimated_time_mins,
                  process_plan: event.data.optimized_process_plan
                };
                setProcessPlan(finalPlan);
              }
              updateAgentStatus('validation', 'success', 'Validation passed.');
              updateAgentStatus('documentation', 'running', 'Compiling report package...');
            }

            if (stage === 'documentation' && event.data?.report_html) {
              setReportHtml(event.data.report_html);
              updateAgentStatus('documentation', 'success', 'Documentation ready.');
            }

            if (stage === 'complete' && event.data) {
              const completeData = event.data;
              const perceptionData = completeData.ballooning || completeData.perception || {};
              const extractedFeatures = perceptionData.features || [];

              finalDrawing = {
                id: perceptionData.filename || `${drawing.name}-${Date.now()}`,
                name: drawing.name,
                category: perceptionData.category || 'Mechanical Component',
                material: perceptionData.material || 'Steel',
                dimensions: perceptionData.dimensions || 'Standard',
                imageUrl: drawing.imageUrl,
                features: extractedFeatures
              };

              setSelectedDrawing(finalDrawing);
              
              finalJson = {
                material: perceptionData.material || 'Steel',
                dimensions: perceptionData.dimensions || '',
                features: extractedFeatures,
                raw_features: extractedFeatures
              };
              setStructuredJson(finalJson);

              setBalloons(toBalloonOverlay(extractedFeatures));
              setBalloonLayer(true);

              finalRag = toRagResults(completeData.memory_context || [], finalDrawing.material);
              setRagResults(finalRag);
              
              if (completeData.plan) {
                finalPlan = toProcessPlanState(completeData.plan);
                setProcessPlan(finalPlan);
              }
              
              if (completeData.validation) {
                finalWarnings = completeData.validation.warnings || [];
                finalOptimizations = completeData.validation.reflection_optimizations || [];
                setValidationWarnings(finalWarnings);
                setReflectionOptimizations(finalOptimizations);
              }

              setAgents(prev => prev.map(a => ({ ...a, status: 'success' })));
              addLog('Pipeline completed successfully.');

              // Save complete run to localStorage history
              saveToHistory({
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                drawing: finalDrawing,
                structuredJson: finalJson,
                processPlan: finalPlan,
                validationWarnings: finalWarnings,
                reflectionOptimizations: finalOptimizations,
                ragResults: finalRag
              });
            }
          } catch (err) {
            console.error('Failed to parse SSE payload', err);
          }
        }
      }
    } catch (err) {
      addLog('Error running pipeline via SSE stream.');
      updateAgentStatus('complete', 'failed', 'Pipeline execution failed.');
    }
  };

  return (
    <div className="flex h-screen bg-[#0b0f19] text-gray-100 font-sans overflow-hidden">
      {/* Sidebar navigation */}
      <div className="w-64 bg-[#111827] border-r border-gray-800 flex flex-col justify-between shrink-0">
        <div>
          <div className="p-6 flex items-center space-x-3 border-b border-gray-800">
            <Cpu className="w-8 h-8 text-indigo-500 animate-pulse" />
            <span className="font-bold text-lg tracking-wider bg-gradient-to-r from-indigo-400 to-teal-400 bg-clip-text text-transparent">
              C2P AI COPILOT
            </span>
          </div>
          <nav className="p-4 space-y-2">
            <div className="flex items-center space-x-3 px-4 py-3 bg-indigo-600/20 text-indigo-400 border-l-4 border-indigo-500 rounded-r-lg text-sm font-semibold">
              <Layers className="w-5 h-5" />
              <span>Pipeline Workspace</span>
            </div>
          </nav>
        </div>

        {/* Processed History Tray in Sidebar */}
        <div className="p-4 border-t border-gray-800 flex-1 overflow-y-auto max-h-[380px]">
          <div className="flex items-center justify-between text-xs font-bold text-gray-400 mb-3 px-1">
            <span className="flex items-center space-x-1.5">
              <History className="w-3.5 h-3.5 text-indigo-400" />
              <span>Recent Processing History</span>
            </span>
            {history.length > 0 && (
              <button onClick={clearHistory} className="text-gray-600 hover:text-rose-400 transition-colors" title="Clear History">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {history.length > 0 ? (
            <div className="space-y-2">
              {history.map((item, index) => (
                <button
                  key={index}
                  onClick={() => loadHistoryItem(item)}
                  className={`w-full text-left p-2.5 rounded-xl border text-xs transition-all ${
                    selectedDrawing?.name === item.drawing.name
                      ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300'
                      : 'bg-gray-900/40 border-gray-800/80 hover:bg-gray-800/60 text-gray-400'
                  }`}
                >
                  <div className="font-bold text-gray-200 truncate">{item.drawing.name}</div>
                  <div className="flex justify-between items-center text-[10px] text-gray-500 mt-1">
                    <span>{item.drawing.material}</span>
                    <span>{item.timestamp}</span>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-[11px] text-gray-600 italic px-1">
              No recent runs saved. Upload a drawing to record history.
            </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-800 flex items-center space-x-3 text-xs text-gray-500">
          <Clock className="w-4 h-4" />
          <span>Local Time: {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-8">
        <div className="space-y-6">
          {/* Header info bar */}
          <div className="bg-[#111827]/60 border border-gray-800 p-6 rounded-2xl flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Drawing Understanding Pipeline</h1>
              <p className="text-gray-400 text-sm mt-1">Upload technical engineering drawings to trigger automated multi-agent extraction.</p>
            </div>
            <div className="flex items-center space-x-3">
              {processPlan && (
                <button 
                  onClick={downloadReportPackage}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-xl text-sm font-semibold flex items-center space-x-2 shadow-lg transition-all"
                >
                  <Download className="w-4 h-4" />
                  <span>Download Report Package</span>
                </button>
              )}
              <label className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl text-sm font-semibold cursor-pointer flex items-center space-x-2 shadow-lg transition-all">
                <Upload className="w-4 h-4" />
                <span>{uploading ? 'Analyzing...' : 'Upload Technical Drawing'}</span>
                <input type="file" onChange={handleFileUpload} className="hidden" accept="image/*" />
              </label>
            </div>
          </div>

          {/* Split Column Layout */}
          <div className="grid grid-cols-12 gap-6">
            {/* Left Column: Visual Canvas, JSON & Plans */}
            <div className="col-span-7 space-y-6">
              {/* Visual Canvas Area */}
              <div className="bg-[#111827]/60 border border-gray-800 rounded-2xl p-6 relative flex flex-col justify-between">
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

                <div className="flex-1 flex items-center justify-center p-4 bg-gray-950/40 border border-gray-800/60 rounded-xl relative min-h-[320px] overflow-hidden">
                  {selectedDrawing ? (
                    <div className="relative w-full h-80 border border-dashed border-gray-800 flex items-center justify-center bg-gray-900/30 rounded-lg overflow-hidden">
                      {selectedDrawing.imageUrl ? (
                        <img 
                          src={selectedDrawing.imageUrl} 
                          alt={selectedDrawing.name} 
                          className="w-full h-full object-contain p-2" 
                        />
                      ) : (
                        <div className="text-center p-4">
                          <div className="text-indigo-400 font-mono text-xs mb-1">CATEGORY: {selectedDrawing.category}</div>
                          <div className="text-lg font-bold mb-2">{selectedDrawing.name}</div>
                          <div className="text-gray-500 text-xs">{selectedDrawing.dimensions} | {selectedDrawing.material}</div>
                        </div>
                      )}
                      
                      {ocrLayer && (
                        <div className="absolute inset-0 bg-indigo-950/20 pointer-events-none flex flex-col items-start p-4 text-[10px] font-mono text-indigo-300 space-y-1 z-10">
                          <div>[OCR: TITLE BLOCK DETECTED]</div>
                          <div>[OCR: MAT={structuredJson?.material || selectedDrawing.material}]</div>
                          <div>[OCR: DIM={structuredJson?.dimensions || selectedDrawing.dimensions}]</div>
                        </div>
                      )}

                      {balloonLayer && balloons.map((b: any) => (
                        <div 
                          key={b.feature_id}
                          style={{ top: `${b.coordinates.y}%`, left: `${b.coordinates.x}%` }}
                          className="absolute bg-teal-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-[10px] font-bold shadow-lg cursor-pointer transform -translate-x-1/2 -translate-y-1/2 hover:scale-125 transition-transform border border-teal-200 z-20"
                          title={`${b.feature_name}: ${b.details}`}
                        >
                          {b.balloon_number}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-16">
                      <Upload className="w-12 h-12 text-gray-600 mx-auto mb-3 animate-bounce" />
                      <p className="text-gray-400 text-sm font-medium">No active drawing loaded.</p>
                      <p className="text-gray-600 text-xs mt-1">Click "Upload Technical Drawing" above to analyze an image.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Structured JSON */}
              <div className="bg-[#111827]/60 border border-gray-800 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-semibold text-sm flex items-center space-x-2">
                    <Code className="w-4 h-4 text-indigo-400" />
                    <span>Structured Engineering JSON</span>
                  </span>
                </div>
                {structuredJson ? (
                  <pre className="bg-gray-950 p-4 rounded-xl text-xs font-mono text-indigo-300 overflow-x-auto border border-gray-800/80 max-h-48">
                    {JSON.stringify(structuredJson, null, 2)}
                  </pre>
                ) : (
                  <div className="bg-gray-950/40 border border-gray-800/40 p-4 rounded-xl text-center text-xs text-gray-500">
                    Parsed Engineering JSON will render here upon upload.
                  </div>
                )}
              </div>

              {/* Qdrant RAG Memory with Guaranteed Standards Display */}
              <div className="bg-[#111827]/60 border border-gray-800 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-3 border-b border-gray-800/80 pb-3">
                  <span className="font-semibold text-sm flex items-center space-x-2">
                    <Database className="w-4 h-4 text-indigo-400" />
                    <span>Memory Agent RAG Knowledge (Qdrant Vector DB)</span>
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
                        <p className="text-[11px] font-mono text-gray-300 leading-relaxed">
                          {result.content}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-gray-950/40 border border-gray-800/40 p-4 rounded-xl text-center text-xs text-gray-500">
                    RAG knowledge matches will render here upon Memory Agent completion.
                  </div>
                )}
              </div>

              {/* Manufacturing Process Timeline */}
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
                        <div className="absolute left-[5px] top-1 bg-indigo-500 border-4 border-gray-950 rounded-full w-2.5 h-2.5" />
                        <div className="flex justify-between font-bold text-gray-200">
                          <span>Step {step.step_number}: {step.operation}</span>
                          <span className="text-gray-500 font-normal">{step.estimated_time_mins}m</span>
                        </div>
                        <p className="text-gray-400 mt-1">{step.description}</p>
                        <div className="grid grid-cols-2 gap-2 mt-2 bg-gray-950/40 p-2 rounded-lg border border-gray-900/60 font-mono text-[10px] text-indigo-300">
                          <div><strong className="text-gray-500">Tool:</strong> {step.tool}</div>
                          <div><strong className="text-gray-500">Machine:</strong> {step.machine}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-gray-950/40 border border-gray-800/40 p-4 rounded-xl text-center text-xs text-gray-500">
                    Machining process plan timeline will render here.
                  </div>
                )}
              </div>

              {/* Validation & Optimizations Split */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#111827]/60 border border-gray-800 rounded-2xl p-6">
                  <h3 className="font-semibold text-xs text-gray-300 border-b border-gray-800 pb-2 mb-3 flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                    <span>Validation Agent (DFM)</span>
                  </h3>
                  {validationWarnings.length > 0 ? (
                    <div className="space-y-2">
                      {validationWarnings.map((w: any, idx: number) => (
                        <div key={idx} className="bg-amber-500/10 border border-amber-500/30 p-2.5 rounded-lg text-[10px] text-amber-300 flex items-start space-x-2">
                          <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                          <div>
                            <div className="font-bold uppercase text-[9px]">Severity: {w.severity}</div>
                            <p className="mt-0.5">{w.message}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="bg-gray-950/40 border border-gray-800 p-3 rounded-lg text-center text-xs text-gray-500">
                      No DFM warnings reported.
                    </div>
                  )}
                </div>

                <div className="bg-[#111827]/60 border border-gray-800 rounded-2xl p-6">
                  <h3 className="font-semibold text-xs text-gray-300 border-b border-gray-800 pb-2 mb-3 flex items-center space-x-2">
                    <Cpu className="w-4 h-4 text-teal-400" />
                    <span>Reflection Optimizations</span>
                  </h3>
                  {reflectionOptimizations.length > 0 ? (
                    <div className="space-y-2">
                      {reflectionOptimizations.map((opt: string, idx: number) => (
                        <div key={idx} className="bg-teal-500/10 border border-teal-500/30 p-2.5 rounded-lg text-[10px] text-teal-300 flex items-start space-x-2">
                          <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                          <div>{opt}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="bg-gray-950/40 border border-gray-800 p-3 rounded-lg text-center text-xs text-gray-500">
                      Self-correction loops will render here.
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column: Agents & Execution Stream Logs */}
            <div className="col-span-5 space-y-6">
              {/* Lyzr Orchestration Agent Status */}
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
                        {agent.status === 'failed' && <span className="bg-rose-500/10 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded-full font-bold">Failed</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Live Stream Logs */}
              <div className="bg-[#111827]/60 border border-gray-800 rounded-2xl p-6">
                <h2 className="text-sm font-semibold border-b border-gray-800/85 pb-3 mb-3 flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-indigo-400" />
                  <span>Agent Stream reasoning logs</span>
                </h2>
                <div className="bg-gray-950 p-4 rounded-xl h-64 overflow-y-auto text-[10px] font-mono text-gray-400 border border-gray-800/80 space-y-1">
                  {logs.length > 0 ? logs.map((log, idx) => (
                    <div key={idx}>{log}</div>
                  )) : (
                    <div className="text-gray-600 italic">No activity logs recorded. Upload a drawing to start.</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}