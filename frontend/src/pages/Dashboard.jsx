import React from "react";
import SectionHeader from "../components/SectionHeader.jsx";
import StatCard from "../components/StatCard.jsx";
import { getToken } from "../api/client.js";

export default function Dashboard() {
  const token = getToken();

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Overview"
        title="Your AI assessment control room"
        subtitle="Track progress across role fit, skill readiness, and adaptive tests."
      />

      {!token && (
        <div className="card gradient-card" style={{ marginBottom: "24px", textAlign: "center", padding: "40px" }}>
          <h2 className="big">Welcome to SkillForge AI</h2>
          <p className="muted" style={{ marginBottom: "24px", fontSize: "1.1rem" }}>
            Join our platform to analyze your resume, match with 30+ tech roles, and generate adaptive roadmaps.
          </p>
          <div style={{ display: "flex", gap: "16px", justifyContent: "center" }}>
            <a className="primary-btn" href="/login" style={{ padding: "12px 32px" }}>Login to your account</a>
            <a className="secondary-btn" href="/register" style={{ padding: "12px 32px" }}>Create free account</a>
          </div>
        </div>
      )}

      <div className="grid-3">
        <StatCard label="Profile readiness" value={token ? "78%" : "--"} hint="Based on last resume scan" />
        <StatCard label="Target role" value={token ? "Machine Learning Engineer" : "Not set"} hint="Last selected role" />
        <StatCard label="Next test" value={token ? "Medium" : "--"} hint="Adaptive difficulty" />
      </div>

      <div className="panel">
        <div>
          <p className="eyebrow">Today's playbook</p>
          <h3>Upload a fresh resume and generate your roadmap.</h3>
          <p className="muted">
            The system aligns your resume with role skills, identifies gaps, and builds an adaptive path.
          </p>
        </div>
        <div className="panel-actions">
          <a className="primary-btn" href="/resume">Upload resume</a>
          <a className="ghost-btn" href="/roadmap">View roadmap</a>
        </div>
      </div>
      <div className="grid-2">
        <div className="card">
          <h3>Skill spotlight</h3>
          <p className="muted">Strengthen Python, SQL, and Statistics to unlock the next difficulty tier.</p>
          <div className="pill-row">
            <span className="pill">Python</span>
            <span className="pill">SQL</span>
            <span className="pill">Statistics</span>
          </div>
        </div>
        <div className="card gradient-card">
          <h3>Adaptive engine status</h3>
          <p>Accuracy trending +8% over the last two tests.</p>
          <p className="muted">Next difficulty will shift to Hard if you maintain 80%+</p>
        </div>
      </div>
    </div>
  );
}
