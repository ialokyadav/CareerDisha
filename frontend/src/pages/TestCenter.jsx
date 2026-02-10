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
    if (!list.length) {
      setError("Provide skills to generate a test.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const data = await api.generateTest({ target_role: targetRole, skills: list, total_questions: 6 });
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
        subtitle="Difficulty adapts based on performance."
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
          Skills (comma-separated)
          <input value={skills} onChange={(e) => setSkills(e.target.value)} placeholder="python, django, rest" />
        </label>
        <button className="primary-btn" onClick={handleGenerate} disabled={loading}>
          {loading ? "Generating..." : "Generate test"}
        </button>
        {error && <p className="error">{error}</p>}
      </div>

      {test && (
        <div className="card">
          <h3>Test questions</h3>
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
        </div>
      )}
    </div>
  );
}
