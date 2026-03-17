import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import SectionHeader from "../components/SectionHeader.jsx";
import StatCard from "../components/StatCard.jsx";
import { api, getToken } from "../api/client.js";

export default function Dashboard() {
  const token = getToken();
  const location = useLocation();
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadSnapshot = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const data = await api.dashboardSnapshot();
      setSnapshot(data);
      setError("");
    } catch (err) {
      try {
        const [profile, extraction] = await Promise.all([
          api.profile(),
          api.getLatestExtraction().catch(() => null),
        ]);
        const fallbackSkills = extraction?.skills || [];
        setSnapshot({
          username: profile?.username || "User",
          target_role: extraction?.prediction?.role || "Not set",
          skills: {
            resume: fallbackSkills.map((s) => String(s).toLowerCase()),
            learned_missing: [],
            learning_missing: [],
            still_missing: [],
          },
        });
        setError("Dashboard endpoint unavailable. Showing fallback data.");
      } catch (_fallbackErr) {
        setError(err.message || "Failed to load dashboard data");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSnapshot();
  }, [token, location.pathname]);

  useEffect(() => {
    if (!token) return;
    const onFocus = () => {
      if (location.pathname === "/dashboard") {
        loadSnapshot();
      }
    };
    const onVisibility = () => {
      if (!document.hidden && location.pathname === "/dashboard") {
        loadSnapshot();
      }
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [token, location.pathname]);

  const username = snapshot?.username || "User";
  const targetRole = snapshot?.target_role || "Not set";
  const resumeSkills = snapshot?.skills?.resume || [];
  const learnedMissing = snapshot?.skills?.learned_missing || [];
  const learningMissing = snapshot?.skills?.learning_missing || [];
  const stillMissing = snapshot?.skills?.still_missing || [];

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Overview"
        title={token ? `Welcome, ${username}` : "Your AI assessment control room"}
        subtitle="Track progress across role fit, skill readiness, and adaptive tests."
      />

      {!token && (
        <div className="card gradient-card" style={{ marginBottom: "24px", textAlign: "center", padding: "40px" }}>
          <img
            src="/logo.png"
            alt="CareerDisha AI logo"
            className="brand-logo"
            style={{ margin: "0 auto 10px" }}
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
          <h2 className="big">Welcome to CareerDisha AI</h2>
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
        <StatCard label="Profile readiness" value={token ? `${Math.min(100, resumeSkills.length * 10)}%` : "--"} hint="Based on extracted resume skills" />
        <StatCard label="Target role" value={token ? targetRole : "Not set"} hint="Last selected role" />
        <StatCard label="Next test" value={token ? "Medium" : "--"} hint="Adaptive difficulty" />
      </div>
      {token && error && <p className="error">{error}</p>}

      <div className="panel">
        <div>
          <p className="eyebrow">Today's playbook</p>
          <h3>Upload a fresh resume and generate your roadmap.</h3>
          <p className="muted">
            The system aligns your resume with role skills, identifies gaps, and builds an adaptive path.
          </p>
        </div>
        <div className="panel-actions dashboard-actions">
          <a className="primary-btn dashboard-action-btn" href="/resume">Upload resume</a>
          <a className="ghost-btn dashboard-action-btn" href="/roadmap">View roadmap</a>
          {token && (
            <button className="ghost-btn dashboard-action-btn" onClick={loadSnapshot} disabled={loading}>
              {loading ? "Refreshing..." : "Refresh dashboard"}
            </button>
          )}
        </div>
      </div>
      <div className="grid-2">
        <div className="card">
          <h3>Skill spotlight</h3>
          {loading && <p className="muted">Loading skills...</p>}
          {!loading && token && (
            <>
              <p className="muted">Resume skills</p>
              <div className="pill-row">
                {(resumeSkills.length ? resumeSkills : ["No resume skills yet"]).map((skill) => (
                  <span key={`resume-${skill}`} className="pill">{skill}</span>
                ))}
              </div>

              <p className="muted" style={{ marginTop: "12px" }}>Learned missing skills</p>
              <div className="pill-row">
                {(learnedMissing.length ? learnedMissing : ["None"]).map((skill) => (
                  <span key={`learned-${skill}`} className="pill">{skill}</span>
                ))}
              </div>

              <p className="muted" style={{ marginTop: "12px" }}>Learning now</p>
              <div className="pill-row">
                {(learningMissing.length ? learningMissing : ["None"]).map((skill) => (
                  <span key={`learning-${skill}`} className="pill primary">{skill}</span>
                ))}
              </div>

              <p className="muted" style={{ marginTop: "12px" }}>Still missing skills</p>
              <div className="pill-row">
                {(stillMissing.length ? stillMissing : ["None"]).map((skill) => (
                  <span key={`missing-${skill}`} className="pill">{skill}</span>
                ))}
              </div>
            </>
          )}
          {!token && <p className="muted">Login to view your skills.</p>}
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
