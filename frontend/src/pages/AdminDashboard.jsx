import React, { useState, useEffect } from "react";
import SectionHeader from "../components/SectionHeader.jsx";
import StatCard from "../components/StatCard.jsx";
import { api } from "../api/client.js";

export default function AdminDashboard() {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [retraining, setRetraining] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [roles, setRoles] = useState([]);

    // Skill Form State
    const [skillText, setSkillText] = useState("");
    const [skillTags, setSkillTags] = useState("");

    // Role Form State
    const [roleTags, setRoleTags] = useState("");
    const [roleName, setRoleName] = useState("");

    // Alignment Form State
    const [alignmentRole, setAlignmentRole] = useState("");
    const [alignmentSkills, setAlignmentSkills] = useState("");

    // Dependency Form State
    const [dependencySkill, setDependencySkill] = useState("");
    const [dependencyPrereqs, setDependencyPrereqs] = useState("");

    // Engine Config State
    const [config, setConfig] = useState(null);
    const [testResults, setTestResults] = useState(null);
    const [runningTests, setRunningTests] = useState(false);

    const fetchStatus = async () => {
        try {
            const [statusData, configData] = await Promise.all([
                api.getTrainingStatus(),
                api.getEngineConfig()
            ]);
            setStatus(statusData);
            setConfig(configData);
            setError("");
        } catch (err) {
            setError(err.message || "Failed to fetch dashboard data");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        api.listRoles().then(setRoles).catch(() => { });
    }, []);

    const handleRetrain = async () => {
        setRetraining(true);
        setMessage("");
        setError("");
        try {
            const result = await api.triggerRetraining();
            setMessage(result.status || "Retraining triggered successfully!");
            fetchStatus();
        } catch (err) {
            setError(err.message || "Failed to trigger retraining");
        } finally {
            setRetraining(false);
        }
    };

    const handleAddSkillData = async (e) => {
        e.preventDefault();
        setMessage("");
        setError("");
        try {
            const skills = skillTags.split(",").map(s => s.trim()).filter(Boolean);
            await api.addManualTrainingData({
                type: "skill",
                text: skillText,
                skills: skills
            });
            setMessage("Skill training data added successfully!");
            setSkillText("");
            setSkillTags("");
            fetchStatus();
        } catch (err) {
            setError(err.message || "Failed to add skill data");
        }
    };

    const handleAddRoleData = async (e) => {
        e.preventDefault();
        setMessage("");
        setError("");
        try {
            const skills = roleTags.split(",").map(s => s.trim()).filter(Boolean);
            await api.addManualTrainingData({
                type: "role",
                role: roleName,
                skills: skills
            });
            setMessage("Role training data added successfully!");
            setRoleTags("");
            setRoleName("");
            fetchStatus();
        } catch (err) {
            setError(err.message || "Failed to add role data");
        }
    };

    const handleAddAlignmentData = async (e) => {
        e.preventDefault();
        setMessage("");
        setError("");
        try {
            const skills = alignmentSkills.split(",").map(s => s.trim()).filter(Boolean);
            await api.addManualTrainingData({
                type: "alignment",
                role: alignmentRole,
                skills: skills
            });
            setMessage("Role alignment updated successfully!");
            setAlignmentRole("");
            setAlignmentSkills("");
            fetchStatus();
        } catch (err) {
            setError(err.message || "Failed to update alignment");
        }
    };

    const handleAddDependencyData = async (e) => {
        e.preventDefault();
        setMessage("");
        setError("");
        try {
            const prereqs = dependencyPrereqs.split(",").map(s => s.trim()).filter(Boolean);
            await api.addManualTrainingData({
                type: "dependency",
                skill: dependencySkill,
                prerequisites: prereqs
            });
            setMessage("Skill dependency updated successfully!");
            setDependencySkill("");
            setDependencyPrereqs("");
            fetchStatus();
        } catch (err) {
            setError(err.message || "Failed to update dependency");
        }
    };

    const handleUpdateConfig = async (e) => {
        e.preventDefault();
        setMessage("");
        setError("");
        try {
            await api.updateEngineConfig(config);
            setMessage("Engine configuration updated successfully!");
            fetchStatus();
        } catch (err) {
            setError(err.message || "Failed to update configuration");
        }
    };

    const handleRunTests = async () => {
        setRunningTests(true);
        setTestResults(null);
        try {
            const result = await api.runSystemTests();
            setTestResults(result);
        } catch (err) {
            setError(err.message || "Failed to run system tests");
        } finally {
            setRunningTests(false);
        }
    };

    if (loading) {
        return (
            <div className="page" style={{ textAlign: "center", padding: "100px" }}>
                <p className="big animate-pulse">Scanning ML infrastructure...</p>
            </div>
        );
    }

    return (
        <div className="page">
            <SectionHeader
                eyebrow="Admin Center"
                title="ML Operations & Training Dashboard"
                subtitle="Monitor training data collection and manage model retraining cycles."
            />

            {error && (
                <div className="panel error-panel" style={{ marginBottom: "24px" }}>
                    <p>{error}</p>
                </div>
            )}

            {message && (
                <div className="panel success-panel" style={{ marginBottom: "24px", borderColor: "var(--success)" }}>
                    <p style={{ color: "var(--success)" }}>{message}</p>
                </div>
            )}

            <div className="grid-2">
                <div className="card">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                        <h3>Skill Extractor Status</h3>
                        <span className={`pill ${status?.skills?.new > 0 ? "active" : ""}`}>
                            {status?.skills?.new > 0 ? "New Data Available" : "Up to date"}
                        </span>
                    </div>
                    <div className="grid-2" style={{ gap: "12px" }}>
                        <div className="stat-mini">
                            <p className="muted small">Total Samples</p>
                            <p className="large">{status?.skills?.total || 0}</p>
                        </div>
                        <div className="stat-mini">
                            <p className="muted small">New Signals</p>
                            <p className="large" style={{ color: status?.skills?.new > 0 ? "var(--primary)" : "inherit" }}>
                                {status?.skills?.new || 0}
                            </p>
                        </div>
                    </div>
                    <p className="muted small" style={{ marginTop: "16px" }}>
                        Signals are collected from manual skill entries and unique resume keywords.
                    </p>
                </div>

                <div className="card">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                        <h3>Role Predictor Status</h3>
                        <span className={`pill ${status?.roles?.new > 0 ? "active" : ""}`}>
                            {status?.roles?.new > 0 ? "New Data Available" : "Up to date"}
                        </span>
                    </div>
                    <div className="grid-2" style={{ gap: "12px" }}>
                        <div className="stat-mini">
                            <p className="muted small">Total Mappings</p>
                            <p className="large">{status?.roles?.total || 0}</p>
                        </div>
                        <div className="stat-mini">
                            <p className="muted small">New Mappings</p>
                            <p className="large" style={{ color: status?.roles?.new > 0 ? "var(--primary)" : "inherit" }}>
                                {status?.roles?.new || 0}
                            </p>
                        </div>
                    </div>
                    <p className="muted small" style={{ marginTop: "16px" }}>
                        Mappings are collected from resume uploads and skill-gap analysis role selections.
                    </p>
                </div>
            </div>

            <div className="grid-2" style={{ marginTop: "24px" }}>
                <div className="card">
                    <h3>Role Skill Alignments</h3>
                    <div className="stat-mini">
                        <p className="muted small">Total Mapped Roles</p>
                        <p className="large">{status?.alignments?.total || 0}</p>
                    </div>
                </div>
                <div className="card">
                    <h3>Skill Dependencies</h3>
                    <div className="stat-mini">
                        <p className="muted small">Total Dependency Rules</p>
                        <p className="large">{status?.dependencies?.total || 0}</p>
                    </div>
                </div>
            </div>

            <div className="grid-2" style={{ marginTop: "32px", gap: "24px" }}>
                <div className="card">
                    <h3>Manual Skill Entry</h3>
                    <p className="muted small" style={{ marginBottom: "16px" }}>Add text snippets and their corresponding skills to improve extraction accuracy.</p>
                    <form onSubmit={handleAddSkillData}>
                        <div style={{ marginBottom: "12px" }}>
                            <label className="small muted" style={{ display: "block", marginBottom: "4px" }}>Resume Text Snippet</label>
                            <textarea
                                className="input-field"
                                style={{ width: "100%", minHeight: "80px", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "12px", color: "white" }}
                                value={skillText}
                                onChange={(e) => setSkillText(e.target.value)}
                                placeholder="e.g. 5 years experience in building scalable web applications using React and Node.js..."
                                required
                            />
                        </div>
                        <div style={{ marginBottom: "20px" }}>
                            <label className="small muted" style={{ display: "block", marginBottom: "4px" }}>Skills (comma separated)</label>
                            <input
                                type="text"
                                className="input-field"
                                style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "10px", color: "white" }}
                                value={skillTags}
                                onChange={(e) => setSkillTags(e.target.value)}
                                placeholder="React, Node.js, Web Development"
                                required
                            />
                        </div>
                        <button type="submit" className="secondary-btn" style={{ width: "100%" }}>Add Skill Sample</button>
                    </form>
                </div>

                <div className="card">
                    <h3>Manual Role Entry</h3>
                    <p className="muted small" style={{ marginBottom: "16px" }}>Add skill combinations and their target roles to improve prediction logic.</p>
                    <form onSubmit={handleAddRoleData}>
                        <div style={{ marginBottom: "12px" }}>
                            <label className="small muted" style={{ display: "block", marginBottom: "4px" }}>Role</label>
                            <select
                                className="input-field"
                                style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "10px", color: "white" }}
                                value={roleName}
                                onChange={(e) => setRoleName(e.target.value)}
                                required
                            >
                                <option value="">Select a role...</option>
                                {roles.map(r => <option key={r} value={r}>{r}</option>)}
                            </select>
                        </div>
                        <div style={{ marginBottom: "20px" }}>
                            <label className="small muted" style={{ display: "block", marginBottom: "4px" }}>Skills (comma separated)</label>
                            <input
                                type="text"
                                className="input-field"
                                style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "10px", color: "white" }}
                                value={roleTags}
                                onChange={(e) => setRoleTags(e.target.value)}
                                placeholder="Python, TensorFlow, Neural Networks"
                                required
                            />
                        </div>
                        <button type="submit" className="secondary-btn" style={{ width: "100%" }}>Add Role Mapping</button>
                    </form>
                </div>
            </div>

            <div className="grid-2" style={{ marginTop: "24px", gap: "24px" }}>
                <div className="card">
                    <h3>Manual Alignment Entry</h3>
                    <p className="muted small" style={{ marginBottom: "16px" }}>Define which skills are required for specific roles in Gap Analysis.</p>
                    <form onSubmit={handleAddAlignmentData}>
                        <div style={{ marginBottom: "12px" }}>
                            <label className="small muted" style={{ display: "block", marginBottom: "4px" }}>Role</label>
                            <select
                                className="input-field"
                                style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "10px", color: "white" }}
                                value={alignmentRole}
                                onChange={(e) => setAlignmentRole(e.target.value)}
                                required
                            >
                                <option value="">Select a role...</option>
                                {roles.map(r => <option key={r} value={r}>{r}</option>)}
                            </select>
                        </div>
                        <div style={{ marginBottom: "20px" }}>
                            <label className="small muted" style={{ display: "block", marginBottom: "4px" }}>Required Skills (comma separated)</label>
                            <input
                                type="text"
                                className="input-field"
                                style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "10px", color: "white" }}
                                value={alignmentSkills}
                                onChange={(e) => setAlignmentSkills(e.target.value)}
                                placeholder="Core Python, Git, SQL"
                                required
                            />
                        </div>
                        <button type="submit" className="secondary-btn" style={{ width: "100%" }}>Update Alignment</button>
                    </form>
                </div>

                <div className="card">
                    <h3>Manual Dependency Entry</h3>
                    <p className="muted small" style={{ marginBottom: "16px" }}>Define prerequisites for skills to build logical learning roadmaps.</p>
                    <form onSubmit={handleAddDependencyData}>
                        <div style={{ marginBottom: "12px" }}>
                            <label className="small muted" style={{ display: "block", marginBottom: "4px" }}>Target Skill</label>
                            <input
                                type="text"
                                className="input-field"
                                style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "10px", color: "white" }}
                                value={dependencySkill}
                                onChange={(e) => setDependencySkill(e.target.value)}
                                placeholder="e.g. Machine Learning"
                                required
                            />
                        </div>
                        <div style={{ marginBottom: "20px" }}>
                            <label className="small muted" style={{ display: "block", marginBottom: "4px" }}>Prerequisites (comma separated)</label>
                            <input
                                type="text"
                                className="input-field"
                                style={{ width: "100%", background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "10px", color: "white" }}
                                value={dependencyPrereqs}
                                onChange={(e) => setDependencyPrereqs(e.target.value)}
                                placeholder="Python, Statistics"
                                required
                            />
                        </div>
                        <button type="submit" className="secondary-btn" style={{ width: "100%" }}>Update Dependency</button>
                    </form>
                </div>
            </div>

            <div className="grid-2" style={{ marginTop: "24px", gap: "24px" }}>
                <div className="card">
                    <h3>Engine Configuration (Tuning)</h3>
                    <p className="muted small" style={{ marginBottom: "16px" }}>Fine-tune model behavior thresholds for adaptive logic and gap analysis.</p>
                    {config && (
                        <form onSubmit={handleUpdateConfig}>
                            <h4 className="small muted">Adaptive Engine</h4>
                            <div className="grid-2" style={{ gap: "12px", marginBottom: "16px" }}>
                                <div>
                                    <label className="small muted">Upgrade Threshold</label>
                                    <input
                                        type="number" step="0.1" max="1" min="0"
                                        className="input-field"
                                        value={config.adaptive_engine.upgrade_threshold}
                                        onChange={(e) => setConfig({ ...config, adaptive_engine: { ...config.adaptive_engine, upgrade_threshold: parseFloat(e.target.value) } })}
                                    />
                                </div>
                                <div>
                                    <label className="small muted">Downgrade Threshold</label>
                                    <input
                                        type="number" step="0.1" max="1" min="0"
                                        className="input-field"
                                        value={config.adaptive_engine.downgrade_threshold}
                                        onChange={(e) => setConfig({ ...config, adaptive_engine: { ...config.adaptive_engine, downgrade_threshold: parseFloat(e.target.value) } })}
                                    />
                                </div>
                            </div>

                            <h4 className="small muted">Skill Gap Analyzer</h4>
                            <div className="grid-2" style={{ gap: "12px", marginBottom: "20px" }}>
                                <div>
                                    <label className="small muted">Weak Threshold</label>
                                    <input
                                        type="number" step="0.1" max="1" min="0"
                                        className="input-field"
                                        value={config.skill_gap_analyzer.weak_threshold}
                                        onChange={(e) => setConfig({ ...config, skill_gap_analyzer: { ...config.skill_gap_analyzer, weak_threshold: parseFloat(e.target.value) } })}
                                    />
                                </div>
                                <div>
                                    <label className="small muted">Missing Threshold</label>
                                    <input
                                        type="number" step="0.1" max="1" min="0"
                                        className="input-field"
                                        value={config.skill_gap_analyzer.missing_threshold}
                                        onChange={(e) => setConfig({ ...config, skill_gap_analyzer: { ...config.skill_gap_analyzer, missing_threshold: parseFloat(e.target.value) } })}
                                    />
                                </div>
                            </div>
                            <button type="submit" className="secondary-btn" style={{ width: "100%" }}>Save Config</button>
                        </form>
                    )}
                </div>

                <div className="card">
                    <h3>ML Engine Test Center</h3>
                    <p className="muted small" style={{ marginBottom: "16px" }}>Execute system-level unit tests to verify engine integrity after training or tuning.</p>
                    <button
                        onClick={handleRunTests}
                        disabled={runningTests}
                        className="secondary-btn"
                        style={{ width: "100%", marginBottom: "16px" }}
                    >
                        {runningTests ? "Running Tests..." : "Run ml_engine/tests.py"}
                    </button>

                    {testResults && (
                        <div className="panel" style={{ background: "rgba(0,0,0,0.3)", borderRadius: "8px", padding: "12px", maxHeight: "250px", overflowY: "auto" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                                <span className={`pill ${testResults.status === "success" ? "active" : "error"}`}>
                                    {testResults.status.toUpperCase()}
                                </span>
                                <span className="muted small">Code: {testResults.returncode}</span>
                            </div>
                            <pre style={{ fontSize: "0.8rem", whiteSpace: "pre-wrap", color: testResults.status === "success" ? "var(--success)" : "#ff6b6b" }}>
                                {testResults.output}
                            </pre>
                        </div>
                    )}
                </div>
            </div>

            <div className="panel gradient-card" style={{ marginTop: "32px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                    <h3>Manual Model Retraining</h3>
                    <p className="muted">
                        Force a retraining of both the Skill Extractor and Role Predictor models using current data.
                    </p>
                </div>
                <button
                    className="primary-btn"
                    onClick={handleRetrain}
                    disabled={retraining}
                    style={{ minWidth: "160px" }}
                >
                    {retraining ? "Training..." : "Trigger Retrain"}
                </button>
            </div>

            <div className="card" style={{ marginTop: "24px" }}>
                <h3>ML Pipeline Logs</h3>
                <div className="panel" style={{ background: "rgba(0,0,0,0.2)", fontFamily: "monospace", fontSize: "0.9rem", padding: "16px" }}>
                    <p className="muted">[INFO] Automatic retrainer threshold: 10 signals</p>
                    <p className="muted">[INFO] Last check completed: Just now</p>
                    {status?.skills?.new >= 10 || status?.roles?.new >= 10 ? (
                        <p style={{ color: "var(--primary)" }}>[WARN] Threshold met. Background retrain pending.</p>
                    ) : (
                        <p style={{ color: "var(--success)" }}>[OK] Data volume stable. No background training needed.</p>
                    )}
                </div>
            </div>
        </div>
    );
}
