
import { useCallback, useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
  Handle,
  Position,
} from "@xyflow/react";
import {
  Activity,
  AlertTriangle,
  AudioLines,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  GitBranch,
  LayoutDashboard,
  Loader2,
  Network,
  Play,
  RefreshCw,
  Search,
  ShieldCheck,
  Upload,
  Workflow,
} from "lucide-react";

import "@xyflow/react/dist/style.css";
import "./App.css";

const API = "http://127.0.0.1:8000";

const NAV_ITEMS = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "graph", label: "Assumption Graph", icon: Network },
  { id: "voice", label: "Voice Intelligence", icon: AudioLines },
  { id: "findings", label: "Findings", icon: AlertTriangle },
  { id: "scenarios", label: "Scenario Simulator", icon: Workflow },
];

function AssumptionNode({ data }) {
  return (
    <div className="assumption-node">
      <Handle
        type="target"
        position={Position.Right}
        style={{ background: "#60a5fa", width: 9, height: 9 }}
        isConnectable={false}
      />

      <Handle
        type="source"
        position={Position.Left}
        style={{ background: "#60a5fa", width: 9, height: 9 }}
        isConnectable={false}
      />

      <div className="node-top">
        <span className="node-department">
          {data.department || "Unassigned"}
        </span>
        <span className="node-id">#{data.id}</span>
      </div>

      <div className="node-subject">
        {data.subject || "Untitled assumption"}
      </div>

      <div className="node-value">
        {data.metric}:{" "}
        <strong>
          {data.value ?? "—"} {data.unit || ""}
        </strong>
      </div>

      <div className="node-bottom">
        <span>{data.assumption_type || "Assumption"}</span>
        <span>{data.review_status || "Pending"}</span>
      </div>
    </div>
  );
}

const nodeTypes = { assumption: AssumptionNode };

function App() {
  const [activePage, setActivePage] = useState("overview");
  const [graph, setGraph] = useState(null);
  const [findings, setFindings] = useState([]);
  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [apiError, setApiError] = useState("");
  const [notice, setNotice] = useState("");

  const [department, setDepartment] = useState("Sales");
  const [speaker, setSpeaker] = useState("");
  const [transcript, setTranscript] = useState("");
  const [audioFile, setAudioFile] = useState(null);
  const [language, setLanguage] = useState("en-IN");
  const [voiceBusy, setVoiceBusy] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [approvingDependency, setApprovingDependency] = useState(null);
  const [approvedDependencyKeys, setApprovedDependencyKeys] = useState([]);

  const [selectedAssumption, setSelectedAssumption] = useState("");
  const [newValue, setNewValue] = useState("");
  const [scenarioBusy, setScenarioBusy] = useState(false);
  const [scenarioResult, setScenarioResult] = useState(null);

  const [findingFilter, setFindingFilter] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  const loadDashboard = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    else setLoading(true);

    setApiError("");

    try {
      const [graphResponse, findingsResponse, scenariosResponse] =
        await Promise.all([
          axios.get(`${API}/api/graph`),
          axios.get(`${API}/api/graph/findings`),
          axios.get(`${API}/api/scenarios`),
        ]);

      setGraph(graphResponse.data);
      setFindings(findingsResponse.data.findings || []);
      setScenarios(scenariosResponse.data.scenarios || []);
    } catch (error) {
      setApiError(
        error.response?.data?.detail ||
        "Unable to connect to the backend. Check that FastAPI is running on port 8000."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  const assumptions = graph?.nodes || [];

  const graphNodes = useMemo(() => {
    const columns = 6;

    return assumptions.map((item, index) => ({
      id: String(item.id),
      type: "assumption",
      position: {
        x: (index % columns) * 300,
        y: Math.floor(index / columns) * 190,
      },
      data: item,
    }));
  }, [assumptions]);

  const graphEdges = useMemo(
    () =>
      (graph?.edges || []).map((edge, index) => ({
        id: `edge-${index}-${edge.source}-${edge.target}`,
        source: String(edge.source),
        target: String(edge.target),
        label: edge.relation || "DEPENDS_ON",
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed },
        style: { strokeWidth: 2 },
      })),
    [graph]
  );

  const filteredFindings = findings.filter((item) => {
    const matchesStatus =
      findingFilter === "all" || item.status === findingFilter;

    const text = `${item.finding_type} ${item.explanation} ${item.severity}`
      .toLowerCase();

    return matchesStatus && text.includes(searchTerm.toLowerCase());
  });

  const openFindings = findings.filter(
    (item) => item.status === "open" || item.status === "under_review"
  ).length;

  const showNotice = (message) => {
    setNotice(message);
    window.setTimeout(() => setNotice(""), 4500);
  };

  const approveDependency = async (candidate) => {
    const key = `${candidate.prerequisite_assumption_id}-${candidate.dependent_assumption_id}`;

    if (approvingDependency || approvedDependencyKeys.includes(key)) {
      return;
    }

    setApprovingDependency(key);

    try {
      await axios.post(`${API}/api/graph/dependencies`, {
        prerequisite_assumption_id: candidate.prerequisite_assumption_id,
        dependent_assumption_id: candidate.dependent_assumption_id,
        rationale: candidate.rationale,
      });

      setApprovedDependencyKeys((previous) => [...previous, key]);
      await loadDashboard(true);

      showNotice("Dependency approved and added to the assumption graph.");
    } catch (error) {
      showNotice(
        error.response?.data?.detail || "Dependency approval failed."
      );
    } finally {
      setApprovingDependency(null);
    }
  };

  const analyzeTranscript = async (textToAnalyze = transcript) => {
    if (!textToAnalyze.trim()) {
      showNotice("Please enter or transcribe a meeting transcript first.");
      return;
    }

    setVoiceBusy(true);
    setAnalysisResult(null);

    try {
      const response = await axios.post(`${API}/api/assumptions/analyze`, {
        department,
        speaker: speaker || null,
        source_type: audioFile ? "audio" : "text",
        language,
        transcript: textToAnalyze,
      });

      setAnalysisResult(response.data);
      setTranscript(textToAnalyze);

      await loadDashboard(true);

      showNotice("Transcript analyzed and assumptions saved successfully.");
    } catch (error) {
      showNotice(
        error.response?.data?.detail || "Transcript analysis failed."
      );
    } finally {
      setVoiceBusy(false);
    }
  };

  const transcribeAudio = async () => {
    if (!audioFile) {
      showNotice("Choose an audio file first.");
      return;
    }

    if (audioFile.size > 15 * 1024 * 1024) {
      showNotice("Audio file must be smaller than 15 MB.");
      return;
    }

    setVoiceBusy(true);
    setAnalysisResult(null);

    try {
      const formData = new FormData();
      formData.append("audio", audioFile);
      formData.append("language_code", language);

      const response = await axios.post(
        `${API}/api/audio/transcribe`,
        formData
      );

      const extractedTranscript =
        response.data.transcript || response.data.text || "";

      if (!extractedTranscript) {
        showNotice("Transcription returned no transcript text.");
      } else {
        setTranscript(extractedTranscript);
        showNotice(
          "Audio transcribed successfully. Review the transcript before analysis."
        );
      }
    } catch (error) {
      showNotice(
        error.response?.data?.detail || "Audio transcription failed."
      );
    } finally {
      setVoiceBusy(false);
    }
  };

  const scanFindings = async () => {
    try {
      const response = await axios.post(
        `${API}/api/graph/contradictions/scan`
      );

      await loadDashboard(true);

      showNotice(response.data.message || "Finding scan completed.");
    } catch (error) {
      showNotice(error.response?.data?.detail || "Finding scan failed.");
    }
  };

  const updateFindingStatus = async (id, status) => {
    try {
      await axios.patch(`${API}/api/graph/findings/${id}/status`, {
        status,
      });

      await loadDashboard(true);

      showNotice(`Finding status updated to ${status.replace("_", " ")}.`);
    } catch (error) {
      showNotice(error.response?.data?.detail || "Status update failed.");
    }
  };

  const simulateScenario = async () => {
    if (!selectedAssumption || !newValue.trim()) {
      showNotice("Select an assumption and enter a new value.");
      return;
    }

    setScenarioBusy(true);
    setScenarioResult(null);

    try {
      const response = await axios.post(`${API}/api/scenarios/simulate`, {
        assumption_id: Number(selectedAssumption),
        new_value: newValue,
      });

      setScenarioResult(response.data);

      await loadDashboard(true);

      showNotice("Scenario simulated and saved.");
    } catch (error) {
      showNotice(error.response?.data?.detail || "Scenario simulation failed.");
    } finally {
      setScenarioBusy(false);
    }
  };

  const pageTitle = NAV_ITEMS.find((item) => item.id === activePage)?.label;

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-logo"><Network size={28} /></div>
        <Loader2 className="spin" size={24} />
        <p>Connecting to AssumptionGraph...</p>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Network size={23} /></div>
          <div>
            <div className="brand-name">AssumptionGraph</div>
            <div className="brand-caption">ENTERPRISE INTELLIGENCE</div>
          </div>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="navigation">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={`nav-item ${activePage === id ? "active" : ""}`}
              onClick={() => setActivePage(id)}
            >
              <Icon size={18} />
              <span>{label}</span>

              {id === "findings" && openFindings > 0 && (
                <span className="nav-count">{openFindings}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="connection-card">
            <span className="connection-dot" />
            <div>
              <strong>
                {apiError ? "Backend disconnected" : "Backend connected"}
              </strong>
              <small>FastAPI · localhost:8000</small>
            </div>
          </div>

          <div className="sidebar-footer">
            <span>ASSUMPTIONGRAPH MVP</span>
            <span>v0.1.0</span>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <div className="breadcrumb">
              Workspace <ChevronRight size={13} /> {pageTitle}
            </div>
            <h1>{pageTitle}</h1>
          </div>

          <div className="topbar-actions">
            <span className="environment-tag">
              <CircleDot size={11} /> LIVE ENVIRONMENT
            </span>

            <button
              className="icon-button"
              onClick={() => loadDashboard(true)}
              title="Refresh dashboard"
              disabled={refreshing}
            >
              <RefreshCw
                size={17}
                className={refreshing ? "spin" : ""}
              />
            </button>
          </div>
        </header>

        {apiError && (
          <div className="error-banner">
            <AlertTriangle size={18} />
            <span>{apiError}</span>
            <button onClick={() => loadDashboard(true)}>Retry</button>
          </div>
        )}

        {notice && <div className="toast-message">{notice}</div>}

        <div className="page-content">
          {activePage === "overview" && (
            <section>
              <div className="welcome-row">
                <div>
                  <div className="eyebrow">
                    ENTERPRISE ASSUMPTION INTELLIGENCE
                  </div>

                  <h2>Understand what your organization believes.</h2>

                  <p>
                    Connect assumptions across teams, identify potential
                    inconsistencies, and explore downstream impacts.
                  </p>
                </div>

                <div className="overview-symbol">
                  <Workflow size={42} />
                </div>
              </div>

              <div className="stats-grid">
                <StatCard
                  icon={Network}
                  label="Assumptions"
                  value={graph?.node_count ?? 0}
                  detail="Recorded in the graph"
                />

                <StatCard
                  icon={GitBranch}
                  label="Dependencies"
                  value={graph?.edge_count ?? 0}
                  detail="Explicitly recorded links"
                />

                <StatCard
                  icon={AlertTriangle}
                  label="Open findings"
                  value={openFindings}
                  detail="Awaiting review"
                />

                <StatCard
                  icon={Activity}
                  label="Scenarios"
                  value={scenarios.length}
                  detail="Saved simulations"
                />
              </div>

              <div className="overview-grid">
                <div className="panel graph-preview">
                  <PanelHeading
                    title="Assumption network"
                    subtitle="Live view of recorded assumptions and dependencies"
                    action="Explore graph"
                    onAction={() => setActivePage("graph")}
                  />

                  {assumptions.length > 0 ? (
                    <div className="mini-graph">
                      <ReactFlow
                        nodes={graphNodes}
                        edges={graphEdges}
                        nodeTypes={nodeTypes}
                        fitView
                        fitViewOptions={{ padding: 0.25 }}
                        nodesDraggable={false}
                        nodesConnectable={false}
                        elementsSelectable={false}
                        proOptions={{ hideAttribution: true }}
                      >
                        <Background />
                      </ReactFlow>
                    </div>
                  ) : (
                    <EmptyState text="No assumptions have been recorded yet. Analyze a transcript to create your first assumptions." />
                  )}

                  <div className="graph-meta">
                    <span>
                      <span className="legend-dot blue" /> Assumptions
                    </span>

                    <span>
                      <span className="legend-line" /> Recorded dependency
                    </span>

                    <span
                      className={
                        graph?.has_cycles ? "warning-text" : "success-text"
                      }
                    >
                      {graph?.has_cycles
                        ? "Cycle detected"
                        : "No graph cycles detected"}
                    </span>
                  </div>
                </div>

                <div className="panel activity-panel">
                  <PanelHeading
                    title="Review queue"
                    subtitle="Findings requiring attention"
                    action="View all"
                    onAction={() => setActivePage("findings")}
                  />

                  {findings.length === 0 ? (
                    <EmptyState text="No saved findings yet. Run a scan to check for potential inconsistencies." />
                  ) : (
                    findings.slice(0, 5).map((item) => (
                      <div className="activity-item" key={item.id}>
                        <span className={`severity-dot ${item.severity}`} />

                        <div className="activity-copy">
                          <strong>{formatLabel(item.finding_type)}</strong>
                          <p>{item.explanation}</p>
                          <small>{formatLabel(item.status)}</small>
                        </div>
                      </div>
                    ))
                  )}

                  <button
                    className="secondary-button full-button"
                    onClick={scanFindings}
                  >
                    <Search size={15} /> Scan for potential contradictions
                  </button>
                </div>
              </div>

              <div className="panel integrity-panel">
                <div className="integrity-icon">
                  <ShieldCheck size={22} />
                </div>

                <div>
                  <strong>Evidence-first intelligence</strong>
                  <p>
                    Findings are potential inconsistencies, not automatically
                    confirmed business facts. Human review remains part of the
                    workflow.
                  </p>
                </div>

                <span className="integrity-tag">HUMAN REVIEW</span>
              </div>
            </section>
          )}

          {activePage === "graph" && (
            <section>
              <PageIntro
                eyebrow="KNOWLEDGE GRAPH"
                title="Explore assumption dependencies"
                description="Inspect assumptions and trace how explicitly recorded dependencies connect teams."
              />

              <div className="graph-toolbar">
                <div className="graph-summary">
                  <span>{graph?.node_count ?? 0} nodes</span>
                  <span>{graph?.edge_count ?? 0} connections</span>
                  <span>
                    {graph?.is_directed ? "Directed graph" : "Undirected graph"}
                  </span>
                </div>

                <span
                  className={
                    graph?.has_cycles ? "warning-text" : "success-text"
                  }
                >
                  {graph?.has_cycles ? "Cycles detected" : "Acyclic graph"}
                </span>
              </div>

              <div className="panel full-graph">
                {graphNodes.length > 0 ? (
                  <ReactFlow
                    nodes={graphNodes}
                    edges={graphEdges}
                    nodeTypes={nodeTypes}
                    fitView
                    fitViewOptions={{ padding: 0.2 }}
                    minZoom={0.2}
                    nodesConnectable={false}
                    proOptions={{ hideAttribution: true }}
                  >
                    <Background />
                    <Controls />
                    <MiniMap zoomable pannable />
                  </ReactFlow>
                ) : (
                  <EmptyState text="No graph nodes available. Analyze a transcript to add assumptions." />
                )}
              </div>

              <p className="helper-text">
                Connections represent dependencies explicitly recorded in your
                database. The graph does not infer missing relationships.
              </p>
            </section>
          )}

          {activePage === "voice" && (
            <section>
              <PageIntro
                eyebrow="GNANI PRISMA · VOICE INTELLIGENCE"
                title="Turn conversations into structured intelligence"
                description="Transcribe meeting audio and extract evidence-backed assumptions for your enterprise graph."
              />

              <div className="voice-layout">
                <div className="panel voice-form">
                  <h3>Meeting source</h3>

                  <p className="panel-description">
                    Provide an audio recording or paste an existing transcript.
                  </p>

                  <label className="field-label">Department</label>

                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="form-control"
                  >
                    {[
                      "Sales",
                      "Operations",
                      "Procurement",
                      "Finance",
                      "Marketing",
                      "Engineering",
                      "Strategy",
                      "Human Resources",
                      "Other",
                    ].map((item) => (
                      <option key={item}>{item}</option>
                    ))}
                  </select>

                  <label className="field-label">Speaker (optional)</label>

                  <input
                    className="form-control"
                    value={speaker}
                    onChange={(e) => setSpeaker(e.target.value)}
                    placeholder="Speaker name or role"
                  />

                  <label className="field-label">Language</label>

                  <select
                    className="form-control"
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                  >
                    <option value="en-IN">English (India)</option>
                    <option value="en-US">English (US)</option>
                    <option value="hi-IN">Hindi (India)</option>
                  </select>

                  <label className="field-label">Upload meeting audio</label>

                  <label className="upload-zone">
                    <Upload size={23} />
                    <strong>
                      {audioFile ? audioFile.name : "Choose an audio file"}
                    </strong>
                    <span>Maximum file size: 15 MB</span>

                    <input
                      type="file"
                      accept="audio/*,.wav,.mp3,.m4a"
                      onChange={(e) =>
                        setAudioFile(e.target.files?.[0] || null)
                      }
                    />
                  </label>

                  <button
                    className="secondary-button full-button"
                    onClick={transcribeAudio}
                    disabled={voiceBusy || !audioFile}
                  >
                    {voiceBusy ? (
                      <Loader2 className="spin" size={16} />
                    ) : (
                      <AudioLines size={16} />
                    )}
                    Transcribe with Gnani Prisma
                  </button>

                  <div className="divider-label">
                    <span>OR ENTER TRANSCRIPT</span>
                  </div>

                  <label className="field-label">Meeting transcript</label>

                  <textarea
                    className="form-control transcript-input"
                    value={transcript}
                    onChange={(e) => setTranscript(e.target.value)}
                    placeholder="Paste meeting statements here. Example: We expect 80% dealer adoption by Q3..."
                  />

                  <button
                    className="primary-button full-button"
                    onClick={() => analyzeTranscript()}
                    disabled={voiceBusy || !transcript.trim()}
                  >
                    {voiceBusy ? (
                      <Loader2 className="spin" size={16} />
                    ) : (
                      <Play size={16} />
                    )}
                    Analyze and extract assumptions
                  </button>
                </div>

                <div className="panel extraction-panel">
                  <div className="result-heading">
                    <div className="result-icon">
                      <BarChart3 size={21} />
                    </div>

                    <div>
                      <h3>Extraction results</h3>
                      <p className="panel-description">
                        Structured assumptions extracted from your source.
                      </p>
                    </div>
                  </div>

                  {analysisResult ? (
                    <>
                      <div className="result-count">
                        <strong>{analysisResult.extracted_count}</strong>
                        <span>assumptions extracted</span>
                        <small>Source #{analysisResult.source_id}</small>
                      </div>

                      {(analysisResult.assumptions || []).map((item) => (
                        <div className="extracted-item" key={item.id}>
                          <div className="extracted-top">
                            <strong>{item.subject}</strong>
                            <span className="status-pill">
                              {formatLabel(item.review_status)}
                            </span>
                          </div>

                          <p>
                            {item.metric}: <b>{item.value} {item.unit || ""}</b>
                          </p>

                          <div className="extracted-meta">
                            <span>{item.department}</span>
                            <span>{formatLabel(item.assumption_type)}</span>
                            <span>
                              Confidence:{" "}
                              {Math.round(
                                (item.extraction_confidence || 0) * 100
                              )}
                              %
                            </span>
                          </div>

                          <blockquote>{item.evidence}</blockquote>
                        </div>
                      ))}

                      {(analysisResult.dependency_candidates || []).length >
                        0 && (
                        <div className="dependency-proposals">
                          <h3>Proposed Dependencies</h3>

                          <p className="panel-description">
                            Review these suggested relationships before adding
                            them to the graph.
                          </p>

                          {analysisResult.dependency_candidates.map(
                            (candidate) => {
                              const key = `${candidate.prerequisite_assumption_id}-${candidate.dependent_assumption_id}`;

                              const isApproved =
                                approvedDependencyKeys.includes(key);

                              const isApproving =
                                approvingDependency === key;

                              return (
                                <div className="extracted-item" key={key}>
                                  <div className="extracted-top">
                                    <strong>
                                      {candidate.prerequisite.subject}
                                      {" → "}
                                      {candidate.dependent.subject}
                                    </strong>

                                    <span className="status-pill">
                                      {isApproved
                                        ? "Approved"
                                        : "Pending review"}
                                    </span>
                                  </div>

                                  <p>
                                    <b>Prerequisite:</b>{" "}
                                    {candidate.prerequisite.value}
                                  </p>

                                  <p>
                                    <b>Dependent:</b>{" "}
                                    {candidate.dependent.metric}
                                    {" — "}
                                    {candidate.dependent.value}
                                  </p>

                                  <blockquote>
                                    {candidate.rationale}
                                  </blockquote>

                                  <p className="helper-text">
                                    <b>Validation required:</b>{" "}
                                    {candidate.review_note}
                                  </p>

                                  <button
                                    className="primary-button full-button"
                                    onClick={() =>
                                      approveDependency(candidate)
                                    }
                                    disabled={
                                      Boolean(approvingDependency) ||
                                      isApproved
                                    }
                                  >
                                    {isApproved
                                      ? "Dependency Approved"
                                      : isApproving
                                        ? "Approving..."
                                        : "Approve Dependency"}
                                  </button>
                                </div>
                              );
                            }
                          )}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="empty-extraction">
                      <div className="empty-icon">
                        <AudioLines size={30} />
                      </div>

                      <strong>Waiting for a source</strong>

                      <p>
                        Upload a recording or enter a transcript. Review the
                        extracted assumptions and their supporting evidence
                        here.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </section>
          )}

          {activePage === "findings" && (
            <section>
              <PageIntro
                eyebrow="CONSISTENCY MONITOR"
                title="Review potential inconsistencies"
                description="Inspect evidence, compare assumptions, and record human review decisions."
              />

              <div className="finding-toolbar panel">
                <div className="search-box">
                  <Search size={16} />

                  <input
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search findings..."
                  />
                </div>

                <select
                  className="form-control filter-select"
                  value={findingFilter}
                  onChange={(e) => setFindingFilter(e.target.value)}
                >
                  <option value="all">All statuses</option>
                  <option value="open">Open</option>
                  <option value="under_review">Under review</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="resolved">Resolved</option>
                  <option value="dismissed">Dismissed</option>
                </select>

                <button className="primary-button" onClick={scanFindings}>
                  <Search size={15} /> Run scan
                </button>
              </div>

              {filteredFindings.length === 0 ? (
                <div className="panel">
                  <EmptyState text="No findings match this view. Run a scan or change the filter." />
                </div>
              ) : (
                <div className="findings-list">
                  {filteredFindings.map((item) => (
                    <article className="panel finding-card" key={item.id}>
                      <div className="finding-card-top">
                        <div className="finding-title">
                          <span className={`severity-dot ${item.severity}`} />

                          <div>
                            <h3>{formatLabel(item.finding_type)}</h3>
                            <small>
                              Finding #{item.id} ·{" "}
                              {formatLabel(item.severity)} severity
                            </small>
                          </div>
                        </div>

                        <span
                          className={`status-pill status-${item.status}`}
                        >
                          {formatLabel(item.status)}
                        </span>
                      </div>

                      <p className="finding-explanation">
                        {item.explanation}
                      </p>

                      <div className="evidence-grid">
                        {(item.evidence || []).map((evidence) => (
                          <div className="evidence-card" key={evidence.id}>
                            <div className="evidence-department">
                              {evidence.department || "Unassigned"} ·
                              Assumption #{evidence.id}
                            </div>

                            <strong>{evidence.subject}</strong>

                            <p>
                              {evidence.metric}: {evidence.value}
                            </p>

                            <blockquote>{evidence.evidence}</blockquote>
                          </div>
                        ))}
                      </div>

                      <div className="finding-actions">
                        <span>
                          {(item.assumption_ids || []).length} linked
                          assumptions
                        </span>

                        <div>
                          <button
                            className="secondary-button small-button"
                            onClick={() =>
                              updateFindingStatus(item.id, "under_review")
                            }
                          >
                            Review
                          </button>

                          <button
                            className="primary-button small-button"
                            onClick={() =>
                              updateFindingStatus(item.id, "confirmed")
                            }
                          >
                            Confirm
                          </button>

                          <button
                            className="text-button"
                            onClick={() =>
                              updateFindingStatus(item.id, "dismissed")
                            }
                          >
                            Dismiss
                          </button>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </section>
          )}

          {activePage === "scenarios" && (
            <section>
              <PageIntro
                eyebrow="WHAT-IF ANALYSIS"
                title="Explore downstream consequences"
                description="Simulate a change to an assumption and inspect the recorded dependencies it may affect."
              />

              <div className="scenario-layout">
                <div className="panel scenario-form">
                  <h3>Configure a scenario</h3>

                  <p className="panel-description">
                    Choose an existing assumption and enter a different value.
                  </p>

                  <label className="field-label">Assumption</label>

                  <select
                    className="form-control"
                    value={selectedAssumption}
                    onChange={(e) => setSelectedAssumption(e.target.value)}
                  >
                    <option value="">Select an assumption...</option>

                    {assumptions.map((item) => (
                      <option key={item.id} value={item.id}>
                        #{item.id} · {item.subject} ({item.department})
                      </option>
                    ))}
                  </select>

                  {selectedAssumption &&
                    (() => {
                      const selected = assumptions.find(
                        (item) =>
                          String(item.id) === selectedAssumption
                      );

                      return selected ? (
                        <div className="selected-assumption">
                          <span>CURRENT VALUE</span>

                          <strong>
                            {selected.value} {selected.unit || ""}
                          </strong>

                          <small>
                            {selected.metric} ·{" "}
                            {selected.period || "No period specified"}
                          </small>
                        </div>
                      ) : null;
                    })()}

                  <label className="field-label">Proposed new value</label>

                  <input
                    className="form-control"
                    value={newValue}
                    onChange={(e) => setNewValue(e.target.value)}
                    placeholder="e.g. October"
                  />

                  <button
                    className="primary-button full-button"
                    onClick={simulateScenario}
                    disabled={
                      scenarioBusy ||
                      !selectedAssumption ||
                      !newValue.trim()
                    }
                  >
                    {scenarioBusy ? (
                      <Loader2 className="spin" size={16} />
                    ) : (
                      <Play size={16} />
                    )}
                    Simulate impact
                  </button>

                  <div className="simulation-note">
                    <ShieldCheck size={17} />

                    <p>
                      Simulation does not modify the original assumption.
                      Results describe possible impacts, not confirmed
                      forecasts.
                    </p>
                  </div>
                </div>

                <div className="panel scenario-results">
                  <h3>Simulation result</h3>

                  <p className="panel-description">
                    The impact analysis will appear here after simulation.
                  </p>

                  {scenarioResult ? (
                    <>
                      <div className="scenario-success">
                        <CheckCircle2 size={18} />
                        Scenario saved · #{scenarioResult.scenario.id}
                      </div>

                      <div className="scenario-comparison">
                        <div>
                          <span>ORIGINAL VALUE</span>
                          <strong>
                            {scenarioResult.scenario.old_value}
                          </strong>
                        </div>

                        <ChevronRight size={19} />

                        <div>
                          <span>PROPOSED VALUE</span>
                          <strong>
                            {scenarioResult.scenario.new_value}
                          </strong>
                        </div>
                      </div>

                      <div className="impact-count">
                        <strong>
                          {scenarioResult.scenario.affected_count}
                        </strong>

                        <span>
                          downstream assumptions potentially affected
                        </span>
                      </div>

                      <p className="impact-summary">
                        {scenarioResult.scenario.impact_summary}
                      </p>

                      {(scenarioResult.scenario.affected_assumptions || []).map(
                        (item) => (
                          <div className="impact-item" key={item.id}>
                            <GitBranch size={16} />

                            <div>
                              <strong>{item.subject}</strong>

                              <small>
                                {item.department} · {item.metric}:{" "}
                                {item.value}
                              </small>
                            </div>
                          </div>
                        )
                      )}

                      {(scenarioResult.scenario.dependency_paths || []).length >
                        0 && (
                        <div className="dependency-paths">
                          <h4>Dependency paths</h4>

                          <p className="path-description">
                            Recorded dependency chains that may be affected
                            by this change.
                          </p>

                          {scenarioResult.scenario.dependency_paths.map(
                            (path, index) => (
                              <div
                                className="dependency-path"
                                key={`${path.assumption_ids.join("-")}-${index}`}
                              >
                                <div className="path-number">
                                  PATH {index + 1}
                                </div>

                                <div className="path-chain">
                                  {path.assumptions.map((step, stepIndex) => (
                                    <div
                                      className="path-step-group"
                                      key={step.id}
                                    >
                                      <div className="path-node">
                                        <strong>{step.subject}</strong>

                                        <small>
                                          {step.department} · {step.metric}:{" "}
                                          {step.value}
                                        </small>
                                      </div>

                                      {stepIndex <
                                        path.assumptions.length - 1 && (
                                        <div className="path-arrow">
                                          <ChevronRight size={17} />
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>

                                <small className="path-depth">
                                  {path.depth} dependency step(s)
                                </small>
                              </div>
                            )
                          )}
                        </div>
                      )}

                      <div className="simulation-note">
                        <ShieldCheck size={17} />

                        <p>
                          Original assumption modified:{" "}
                          {scenarioResult.original_assumption_modified
                            ? "Yes"
                            : "No"}
                        </p>
                      </div>
                    </>
                  ) : (
                    <div className="empty-extraction">
                      <div className="empty-icon">
                        <Workflow size={30} />
                      </div>

                      <strong>Ready to simulate</strong>

                      <p>
                        Configure a scenario to see which downstream
                        assumptions may be affected.
                      </p>
                    </div>
                  )}
                </div>
              </div>

              <div className="panel history-panel">
                <PanelHeading
                  title="Simulation history"
                  subtitle="Previously saved what-if scenarios"
                />

                {scenarios.length === 0 ? (
                  <EmptyState text="No saved scenarios yet." />
                ) : (
                  scenarios.map((item) => (
                    <div className="history-item" key={item.id}>
                      <div className="history-icon">
                        <Workflow size={17} />
                      </div>

                      <div>
                        <strong>
                          {item.subject ||
                            `Assumption #${item.changed_assumption_id}`}
                        </strong>

                        <p>
                          {item.old_value} → {item.new_value}
                        </p>

                        <small>{item.impact_summary}</small>
                      </div>

                      <span className="history-count">
                        {(item.affected_assumption_ids || []).length} impacts
                      </span>
                    </div>
                  ))
                )}
              </div>
            </section>
          )}
        </div>

        <footer className="main-footer">
          <span>AssumptionGraph · Enterprise Assumption Intelligence</span>
          <span>Evidence-backed · Human-reviewed · Explainable</span>
        </footer>
      </main>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, detail }) {
  return (
    <div className="panel stat-card">
      <div className="stat-top">
        <span>{label}</span>
        <div className="stat-icon">
          <Icon size={18} />
        </div>
      </div>

      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

function PanelHeading({ title, subtitle, action, onAction }) {
  return (
    <div className="panel-heading">
      <div>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>

      {action && (
        <button className="text-button" onClick={onAction}>
          {action} <ChevronRight size={14} />
        </button>
      )}
    </div>
  );
}

function PageIntro({ eyebrow, title, description }) {
  return (
    <div className="page-intro">
      <div className="eyebrow">{eyebrow}</div>
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  );
}

function EmptyState({ text }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">
        <Network size={25} />
      </div>
      <p>{text}</p>
    </div>
  );
}

function formatLabel(value) {
  return String(value || "unknown")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default App;
