import React, { useState } from "react";
import SectionHeader from "../components/SectionHeader.jsx";
import { api } from "../api/client.js";

export default function RolePrediction() {
  const [skills, setSkills] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [latestSkills, setLatestSkills] = useState(null);

  const handlePredict = async (manualList = null) => {
    const list = manualList || skills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    if (!list.length) {
      setError("Enter at least one skill or use your resume.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const data = await api.predictRole({ skills: list });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleMatchFromResume = async () => {
    setError("");
    setLoading(true);
    try {
      const data = await api.getLatestExtraction();
      if (data.skills?.length > 0) {
        setSkills(data.skills.join(", "));
        handlePredict(data.skills);
      } else {
        setError("No skills found in your latest resume. Please upload a resume first.");
      }
    } catch (err) {
      setError(err.message === "no previous extraction found"
        ? "No resume found. Please upload your resume in the Resume section."
        : err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Role match"
        title="Predict the best-fit role"
        subtitle="Match your skills against 30+ tech roles using our ML engine."
      />

      <div className="grid-2">
        <div className="card">
          <h3>Quick Match</h3>
          <p className="muted">Use extraction results from your latest resume upload for an instant prediction.</p>
          <button className="primary-btn" onClick={handleMatchFromResume} disabled={loading} style={{ width: "100%", marginTop: "16px" }}>
            {loading ? "Processing..." : "Match from Resume"}
          </button>
        </div>

        <div className="card">
          <h3>Manual Match</h3>
          <label>
            Skills (comma-separated)
            <input
              value={skills}
              onChange={(e) => setSkills(e.target.value)}
              placeholder="e.g. python, django, aws"
            />
          </label>
          <button className="secondary-btn" onClick={() => handlePredict()} disabled={loading} style={{ width: "100%" }}>
            Predict from list
          </button>
        </div>
      </div>

      {error && <p className="error card">{error}</p>}

      {result && (
        <div className="card gradient-card" style={{ marginTop: "24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <p className="eyebrow">Top Match</p>
              <h1 className="big" style={{ margin: "4px 0" }}>{result.predicted_role}</h1>
              <p className="pill primary">Best Fit</p>
            </div>
            <div style={{ textAlign: "right" }}>
              <span className="big" style={{ color: "var(--primary)", fontSize: "3rem" }}>
                {(result.confidence * 100).toFixed(0)}%
              </span>
              <p className="eyebrow" style={{ marginBottom: 0 }}>Match Score</p>
            </div>
          </div>

          {result.matched_skills && result.matched_skills.length > 0 && (
            <div style={{ marginTop: "24px" }}>
              <p className="eyebrow">Matched Skills for this Role</p>
              <div className="pill-row">
                {result.matched_skills.map(s => (
                  <span key={s} className="pill success">{s}</span>
                ))}
              </div>
            </div>
          )}

          <div style={{ marginTop: "24px", paddingTop: "16px", borderTop: "1px solid rgba(255,255,255,0.1)" }}>
            <p className="muted" style={{ fontSize: "0.9rem" }}>
              Based on your skills: {result.skills.join(", ")}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
