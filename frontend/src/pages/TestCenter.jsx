import React, { useState } from "react";
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

export default function TestCenter() {
  const [targetRole, setTargetRole] = useState("Machine Learning Engineer");
  const [skills, setSkills] = useState("");
  const [testMode, setTestMode] = useState("roadmap_step");
  const [test, setTest] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    const list = skills
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    if (testMode === "gap_based" && !list.length) {
      setError("Provide skills to generate a gap-based test.");
      return;
    }

    setError("");
    setLoading(true);
    try {
      const payload = {
        target_role: targetRole,
        mode: testMode,
        total_questions: 6,
      };
      if ((testMode === "existing_skills" || testMode === "gap_based") && list.length) {
        payload.skills = list;
      }
      const data = await api.generateTest(payload);
      setTest(data);
      setAnswers({});
      setResult(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!test) return;
    setLoading(true);
    try {
      const data = await api.submitTest({ test_id: test.test_id, answers });
      setResult(data.result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Adaptive tests"
        title="Generate and complete a personalized test"
        subtitle="Test by active roadmap step or your existing skills."
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
        <label>
          Test mode
          <select value={testMode} onChange={(e) => setTestMode(e.target.value)}>
            <option value="roadmap_step">Roadmap step test</option>
            <option value="existing_skills">Existing skills test</option>
            <option value="gap_based">Gap-based test</option>
          </select>
        </label>
        <label>
          Skills (comma-separated)
          <input
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
            placeholder={
              testMode === "roadmap_step"
                ? "optional for roadmap mode"
                : "python, django, rest"
            }
          />
        </label>
        <button className="primary-btn" onClick={handleGenerate} disabled={loading}>
          {loading ? "Generating..." : "Generate test"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>

      {test && (
        <div className="card">
          <h3>Test questions</h3>
          <p className="muted">
            Mode: {test.mode}
            {test.roadmap_phase ? ` | Step: ${test.roadmap_phase}` : ""}
          </p>
          {test.questions.map((q) => (
            <div key={q._id} className="question-block">
              <p>{q.question}</p>
              <div className="option-grid">
                {q.options.map((opt) => (
                  <label key={opt} className="option">
                    <input
                      type="radio"
                      name={q._id}
                      value={opt}
                      checked={answers[q._id] === opt}
                      onChange={() => setAnswers({ ...answers, [q._id]: opt })}
                    />
                    {opt}
                  </label>
                ))}
              </div>
            </div>
          ))}
          <button className="primary-btn" onClick={handleSubmit} disabled={loading}>
            {loading ? "Submitting..." : "Submit answers"}
          </button>
        </div>
      )}

      {result && (
        <div className="card">
          <h3>Results</h3>
          <p className="big">Accuracy: {(result.accuracy * 100).toFixed(1)}%</p>
          <p className="muted">Next difficulty: {result.next_difficulty}</p>
          {result.phase_result && (
            <p className="muted">
              {result.phase_result.passed
                ? `Step "${result.phase_result.phase}" passed.`
                : `Step "${result.phase_result.phase}" not passed.`}
              {" "}
              Next active step: {result.phase_result.active_phase || "All steps completed"}.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
