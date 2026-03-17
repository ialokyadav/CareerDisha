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
  const [targetRole, setTargetRole] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingTest, setPendingTest] = useState(null);
  const [pendingAnswers, setPendingAnswers] = useState({});
  const [pendingTestResult, setPendingTestResult] = useState(null);
  const [pendingTestLoading, setPendingTestLoading] = useState(false);
  const [pendingTestError, setPendingTestError] = useState("");

  useEffect(() => {
    if (location.state?.target_role) {
      setTargetRole(location.state.target_role);
      // Auto-trigger generation if navigating from Skill Gap
      handleGenerate(location.state.target_role, location.state.skills);
    }
  }, [location.state]);

  const handleGenerate = async (roleOverride = null, skillsOverride = null) => {
    setError("");
    setLoading(true);
    try {
      const isEventObject =
        roleOverride &&
        typeof roleOverride === "object" &&
        typeof roleOverride.preventDefault === "function";
      const normalizedRoleOverride = isEventObject ? null : roleOverride;
      const role = normalizedRoleOverride || targetRole;

      const payload = {};
      if (role) {
        payload.target_role = role;
      }
      if (skillsOverride) {
        const skillsList = typeof skillsOverride === 'string'
          ? skillsOverride.split(',').map(s => s.trim()).filter(Boolean)
          : Array.isArray(skillsOverride) ? skillsOverride : [];
        if (skillsList.length > 0) {
          payload.user_skills = skillsList;
        }
      }

      const data = await api.generateRoadmap(payload);
      setResult(data);
      setPendingTest(null);
      setPendingAnswers({});
      setPendingTestResult(null);
      setPendingTestError("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePendingSkillTest = async () => {
    if (!result?.skills_snapshot?.missing_skills?.length) {
      setPendingTestError("No pending skills found for test generation.");
      return;
    }

    setPendingTestError("");
    setPendingTestLoading(true);
    try {
      const data = await api.generateTest({
        target_role: result.target_role || targetRole,
        mode: "existing_skills",
        skills: result.skills_snapshot.missing_skills,
        total_questions: 10,
      });
      setPendingTest(data);
      setPendingAnswers({});
      setPendingTestResult(null);
    } catch (err) {
      setPendingTestError(err.message);
    } finally {
      setPendingTestLoading(false);
    }
  };

  const handleSubmitPendingSkillTest = async () => {
    if (!pendingTest) return;

    setPendingTestError("");
    setPendingTestLoading(true);
    try {
      const data = await api.submitTest({
        test_id: pendingTest.test_id,
        answers: pendingAnswers,
        skill_pass_threshold: 0.75,
      });
      setPendingTestResult(data.result);
      await handleGenerate(result?.target_role || targetRole);
    } catch (err) {
      setPendingTestError(err.message);
    } finally {
      setPendingTestLoading(false);
    }
  };

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Roadmap"
        title="Generate a personalized role roadmap"
        subtitle="Generate step-wise roadmap from your extracted or provided skills."
      />
      <div className="card">
        <label>
          Target role
          <select value={targetRole} onChange={(e) => setTargetRole(e.target.value)}>
            <option value="">-- No target role --</option>
            {ROLE_OPTIONS.map((role) => (
              <option key={role} value={role}>{role}</option>
            ))}
          </select>
        </label>
        <button className="primary-btn" onClick={() => handleGenerate()} disabled={loading}>
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
                {result.role_source && (
                  <p className="muted" style={{ marginTop: "6px" }}>
                    Role source: {result.role_source === "predicted" ? "Predicted from your skills" : "Selected target role"}
                  </p>
                )}
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
          {result.skills_snapshot?.matched_skills?.length > 0 && (
            <div className="card">
              <h3>Completed Skills</h3>
              <div className="pill-row">
                {result.skills_snapshot.matched_skills.map((skill) => (
                  <span key={`completed-${skill}`} className="pill primary">
                    {skill}
                    {result.skills_snapshot?.completed_skill_scores?.[skill] !== undefined
                      ? ` (${result.skills_snapshot.completed_skill_scores[skill]}%)`
                      : ""}
                  </span>
                ))}
              </div>
            </div>
          )}
          {result.skills_snapshot?.in_progress_skills?.length > 0 && (
            <div className="card">
              <h3>In Progress Skills</h3>
              <div className="pill-row">
                {result.skills_snapshot.in_progress_skills.map((skill) => (
                  <span key={`progress-${skill}`} className="pill warning">{skill}</span>
                ))}
              </div>
            </div>
          )}
          {result.skills_snapshot?.missing_skills?.length > 0 && (
            <div className="card">
              <h3>Pending Skills</h3>
              <div className="pill-row">
                {result.skills_snapshot.missing_skills.map((skill) => (
                  <span key={`missing-${skill}`} className="pill danger">{skill}</span>
                ))}
              </div>
            </div>
          )}
          {result.skills_snapshot?.missing_skills?.length > 0 && (
            <div className="card">
              <div className="list-row" style={{ alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
                <h3 style={{ margin: 0 }}>Pending Skill Test</h3>
                <button
                  className="primary-btn"
                  onClick={handleGeneratePendingSkillTest}
                  disabled={pendingTestLoading}
                >
                  {pendingTestLoading ? "Preparing..." : "Generate Pending Skills Test"}
                </button>
              </div>
              <p className="muted">Score 75% or above in tested pending skills to auto-mark them as completed.</p>
              {pendingTestError && <p className="error">{pendingTestError}</p>}

              {pendingTest && (
                <div style={{ marginTop: "12px" }}>
                  <p className="muted">
                    Questions: {pendingTest.questions?.length || 0} | Skills covered: {(pendingTest.skills_covered || []).join(", ")}
                  </p>
                  {(pendingTest.questions || []).map((q) => (
                    <div key={q._id} className="question-block">
                      <p>{q.question}</p>
                      <div className="option-grid">
                        {q.options.map((opt) => (
                          <label key={`${q._id}-${opt}`} className="option">
                            <input
                              type="radio"
                              name={q._id}
                              value={opt}
                              checked={pendingAnswers[q._id] === opt}
                              onChange={() => setPendingAnswers({ ...pendingAnswers, [q._id]: opt })}
                            />
                            {opt}
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                  <button className="primary-btn" onClick={handleSubmitPendingSkillTest} disabled={pendingTestLoading}>
                    {pendingTestLoading ? "Submitting..." : "Submit Pending Skills Test"}
                  </button>
                </div>
              )}

              {pendingTestResult && (
                <div style={{ marginTop: "12px" }}>
                  <p className="big">Latest test score: {(pendingTestResult.accuracy * 100).toFixed(1)}%</p>
                  <p className="muted">
                    {(pendingTestResult.accuracy * 100) >= 75
                      ? "Eligible skills were marked completed."
                      : "Below 75%, pending skills stay in progress/pending."}
                  </p>
                </div>
              )}
            </div>
          )}
          {result.progress?.phases?.length > 0 && (
            <div className="card">
              <h3>Step-wise Progress</h3>
              <div className="form" style={{ marginTop: "12px" }}>
                {result.progress.phases.map((phase) => (
                  <div key={phase.phase} className="list-row" style={{ alignItems: "center" }}>
                    <span>{phase.phase}</span>
                    <span className="badge">
                      {phase.status}
                    </span>
                  </div>
                ))}
              </div>
              <p className="muted" style={{ marginTop: "10px" }}>
                Active step: {result.progress.active_phase || "All steps completed"}
              </p>
            </div>
          )}

          <div className="roadmap-grid">
            {result.roadmap.map((phase) => (
              <div key={phase.phase} className="card">
                <p className="eyebrow">{phase.phase}</p>
                <h4>{phase.description}</h4>
                <div className="form" style={{ marginTop: "16px" }}>
                  {phase.skills
                    .filter((skill) => skill.status !== "completed")
                    .map((skill) => (
                      <div key={skill.name} className="list-row" style={{ alignItems: "center" }}>
                        <span>{skill.name}</span>
                        <span className={`badge ${skill.status}`}>
                          {skill.status === "in_progress" && "🟡 In Progress"}
                          {skill.status === "pending" && "❌ Pending"}
                        </span>
                      </div>
                    ))}
                  {phase.skills.every((skill) => skill.status === "completed") && (
                    <p className="muted">All skills in this phase are completed.</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
