import React from "react";

export default function StatCard({ label, value, hint }) {
  return (
    <div className="card stat-card">
      <div>
        <p className="muted">{label}</p>
        <h3>{value}</h3>
      </div>
      {hint && <p className="hint">{hint}</p>}
    </div>
  );
}
