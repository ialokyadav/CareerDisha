import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import SectionHeader from "../components/SectionHeader.jsx";
import { api } from "../api/client.js";

export default function SkillGap() {
  const navigate = useNavigate();
  const [skills, setSkills] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [predictedRole, setPredictedRole] = useState("");
  const [roles, setRoles] = useState([]);
  const [targetResult, setTargetResult] = useState(null);
  const [predictedResult, setPredictedResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // 1. Fetch available roles
    api.listRoles()
      .then(data => {
        setRoles(data.roles);
        if (data.roles.length > 0) {
          setTargetRole(data.roles[0]);
        }
      })
      .catch(err => setError("Failed to load roles: " + err.message));

    // 2. Auto-populate from latest extraction if available
    api.getLatestExtraction()
      .then(data => {
        if (data.skills?.length > 0) {
          setSkills(data.skills.join(", "));
        }
        if (data.prediction?.role) {
          setPredictedRole(data.prediction.role);
        }
      })
      .catch(() => {
        // Silent fail: it's okay if there's no previous extraction
      });
  }, []);

  const handleAnalyze = async () => {
    const list = skills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    if (!list.length) {
      setError("Enter skills or use your resume extraction.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const targetResponse = await api.skillGap({ skills: list, target_role: targetRole });
      setTargetResult(targetResponse);

      if (predictedRole && predictedRole !== targetRole) {
        const predictedResponse = await api.skillGap({ skills: list, target_role: predictedRole });
        setPredictedResult(predictedResponse);
      } else {
        setPredictedResult(null);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoToRoadmap = (role, currentSkills) => {
    navigate("/roadmap", { state: { target_role: role, skills: currentSkills } });
  };

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Skill gap"
        title="Analyze your path"
        subtitle="Compare your profile against your target role and your ML-predicted role."
      />

      <div className="card">
        <div className="grid-2">
          <label>
            Target role
            <select value={targetRole} onChange={(e) => setTargetRole(e.target.value)}>
              {roles.map((role) => (
                <option key={role} value={role}>{role}</option>
              ))}
            </select>
          </label>
          <label>
            Your current skills
            <input
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
              placeholder="e.g. python, django, rest api"
            />
          </label>
        </div>
        {predictedRole && (
          <p className="muted" style={{ marginTop: "8px" }}>
            💡 Your predicted role is <strong>{predictedRole}</strong>
          </p>
        )}
        <button className="primary-btn" onClick={handleAnalyze} disabled={loading} style={{ width: "100%", marginTop: "16px" }}>
          {loading ? "Calculating Gaps..." : "Analyze Skill Gaps"}
        </button>
        {error && <p className="error card" style={{ marginTop: "16px" }}>{error}</p>}
      </div>

      <div className="grid-2" style={{ marginTop: "24px", alignItems: "start" }}>
        {/* Target Role Comparison */}
        {targetResult && (
          <div className="card" style={{ borderTop: "4px solid var(--primary)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ margin: 0 }}>Target: {targetRole}</h3>
              <span className="pill primary">Desirable</span>
            </div>

            <div className="form">
              <div className="list-row">
                <span>Matched</span>
                <span style={{ color: "var(--success)" }}>{targetResult.matched_skills.length}</span>
              </div>
              <div className="list-row">
                <span>Missing</span>
                <span style={{ color: "var(--danger)" }}>{targetResult.missing_skills.length}</span>
              </div>
            </div>

            <div style={{ marginTop: "24px" }}>
              <p className="eyebrow" style={{ color: "var(--danger)" }}>Missing Skills & Knowledge</p>
              <div className="pill-row">
                {targetResult.missing_skills.map(s => (
                  <span key={s} className="pill danger">{s}</span>
                ))}
                {targetResult.missing_skills.length === 0 && <p className="muted">Zero gaps found!</p>}
              </div>
            </div>

            <button
              className="primary-btn"
              onClick={() => handleGoToRoadmap(targetRole, skills)}
              style={{ width: "100%", marginTop: "24px" }}
            >
              Roadmap for {targetRole}
            </button>
          </div>
        )}

        {/* Predicted Role Comparison */}
        {predictedResult && (
          <div className="card" style={{ borderTop: "4px solid #8b5cf6" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h3 style={{ margin: 0 }}>Predicted: {predictedRole}</h3>
              <span className="pill" style={{ backgroundColor: "#8b5cf6", color: "white" }}>ML Engine Choice</span>
            </div>

            <div className="form">
              <div className="list-row">
                <span>Matched</span>
                <span style={{ color: "var(--success)" }}>{predictedResult.matched_skills.length}</span>
              </div>
              <div className="list-row">
                <span>Missing</span>
                <span style={{ color: "var(--danger)" }}>{predictedResult.missing_skills.length}</span>
              </div>
            </div>

            <div style={{ marginTop: "24px" }}>
              <p className="eyebrow" style={{ color: "var(--danger)" }}>Missing Skills & Knowledge</p>
              <div className="pill-row">
                {predictedResult.missing_skills.map(s => (
                  <span key={s} className="pill danger">{s}</span>
                ))}
                {predictedResult.missing_skills.length === 0 && <p className="muted">Zero gaps found!</p>}
              </div>
            </div>

            <button
              className="secondary-btn"
              onClick={() => handleGoToRoadmap(predictedRole, skills)}
              style={{ width: "100%", marginTop: "24px" }}
            >
              Roadmap for {predictedRole}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
