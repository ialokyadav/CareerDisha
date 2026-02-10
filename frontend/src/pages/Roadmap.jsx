import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import SectionHeader from "../components/SectionHeader.jsx";
import { api } from "../api/client.js";

const ROLE_OPTIONS = [
  "Software Developer",
  "Web Developer",
  "Backend Developer",
  "Frontend Developer",
  "Full Stack Developer",
  "Data Scientist",
  "Data Analyst",
  "Machine Learning Engineer",
  "AI Engineer",
  "Cloud Engineer",
  "DevOps Engineer",
  "Cyber Security Analyst",
  "Mobile App Developer",
  "System Engineer"
];

export default function Roadmap() {
  const location = useLocation();
  const [targetRole, setTargetRole] = useState("Machine Learning Engineer");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (location.state?.target_role) {
      setTargetRole(location.state.target_role);
      // Auto-trigger generation if navigating from Skill Gap
      handleGenerate(location.state.target_role);
    }
  }, [location.state]);

  const handleGenerate = async (roleOverride = null) => {
    setError("");
    setLoading(true);
    try {
      const role = roleOverride || targetRole;
      const data = await api.generateRoadmap({ target_role: role });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Roadmap"
        title="Generate a personalized role roadmap"
        subtitle="Requires a saved skill gap for the target role."
      />
      <div className="card">
        <label>
          Target role
          <select value={targetRole} onChange={(e) => setTargetRole(e.target.value)}>
            {ROLE_OPTIONS.map((role) => (
              <option key={role} value={role}>{role}</option>
            ))}
          </select>
        </label>
        <button className="primary-btn" onClick={handleGenerate} disabled={loading}>
          {loading ? "Generating..." : "Generate roadmap"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>
      {result && (
        <>
          <div className="card gradient-card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <div>
                <h3 className="big">{result.target_role} Roadmap</h3>
                <p className="muted">Your journey to becoming a {result.target_role}</p>
              </div>
              <div style={{ textAlign: "right" }}>
                <span className="big" style={{ color: "var(--primary)" }}>{result.summary.completion_percentage}%</span>
                <p className="eyebrow" style={{ marginBottom: 0 }}>Progress</p>
              </div>
            </div>
            <div className="progress-container">
              <div
                className="progress-bar"
                style={{ width: `${result.summary.completion_percentage}%` }}
              ></div>
            </div>
            <div className="grid-3" style={{ marginTop: "20px" }}>
              <div className="stat-card">
                <p className="eyebrow">Completed</p>
                <h3>{result.summary.completed_skills_count}</h3>
              </div>
              <div className="stat-card">
                <p className="eyebrow">In Progress</p>
                <h3>{result.summary.in_progress_skills_count}</h3>
              </div>
              <div className="stat-card">
                <p className="eyebrow">Pending</p>
                <h3>{result.summary.pending_skills_count}</h3>
              </div>
            </div>
          </div>

          {result.next_recommended_skills?.length > 0 && (
            <div className="card">
              <h3>Next Recommended Skills</h3>
              <div className="pill-row">
                {result.next_recommended_skills.map((skill) => (
                  <span key={skill} className="pill primary">{skill}</span>
                ))}
              </div>
            </div>
          )}

          <div className="roadmap-grid">
            {result.roadmap.map((phase) => (
              <div key={phase.phase} className="card">
                <p className="eyebrow">{phase.phase}</p>
                <h4>{phase.description}</h4>
                <div className="form" style={{ marginTop: "16px" }}>
                  {phase.skills.map((skill) => (
                    <div key={skill.name} className="list-row" style={{ alignItems: "center" }}>
                      <span>{skill.name}</span>
                      <span className={`badge ${skill.status}`}>
                        {skill.status === "completed" && "✅ Completed"}
                        {skill.status === "in_progress" && "🟡 In Progress"}
                        {skill.status === "pending" && "❌ Pending"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
