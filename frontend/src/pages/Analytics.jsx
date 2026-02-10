import React, { useEffect, useState } from "react";
import SectionHeader from "../components/SectionHeader.jsx";
import { api } from "../api/client.js";

export default function Analytics() {
  const [history, setHistory] = useState([]);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const [histData, summaryData] = await Promise.all([
          api.performanceHistory(),
          api.performanceSummary()
        ]);
        setHistory(histData.history || []);
        setSummary(summaryData.skill_accuracy || {});
      } catch (err) {
        setError(err.message);
      }
    };
    load();
  }, []);

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Analytics"
        title="Performance trends and skill accuracy"
        subtitle="Your adaptive learning insights over time."
      />
      {error && <p className="error">{error}</p>}
      <div className="grid-2">
        <div className="card">
          <h3>Recent attempts</h3>
          {history.length === 0 && <p className="muted">No attempts yet.</p>}
          {history.map((item) => (
            <div key={item._id} className="list-row">
              <div>
                <p className="muted">{item.role}</p>
                <p>Accuracy: {(item.accuracy * 100).toFixed(1)}%</p>
              </div>
              <span className="pill soft">{item.difficulty}</span>
            </div>
          ))}
        </div>
        <div className="card">
          <h3>Skill accuracy</h3>
          {summary && Object.keys(summary).length === 0 && <p className="muted">No skill data yet.</p>}
          {summary && Object.entries(summary).map(([skill, value]) => (
            <div key={skill} className="list-row">
              <span>{skill}</span>
              <span className="pill">{(value * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
