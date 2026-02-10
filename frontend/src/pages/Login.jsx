import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api, setToken } from "../api/client.js";

export default function Login() {
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const [mode, setMode] = useState("user"); // 'user' or 'admin'

  const handleChange = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api.login(form);
      setToken(data.access);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-layout">
      <div className="auth-panel">
        <div className="tab-row" style={{ marginBottom: "24px" }}>
          <button
            className={`tab-btn ${mode === "user" ? "active" : ""}`}
            onClick={() => setMode("user")}
          >
            User Login
          </button>
          <button
            className={`tab-btn ${mode === "admin" ? "active" : ""}`}
            onClick={() => setMode("admin")}
          >
            Admin Access
          </button>
        </div>

        {mode === "user" ? (
          <>
            <p className="eyebrow">Welcome back</p>
            <h1>Enter the assessment studio.</h1>
            <p className="muted">Sign in to continue your adaptive learning journey.</p>
            <form className="form" onSubmit={handleSubmit}>
              <label>
                Username
                <input name="username" value={form.username} onChange={handleChange} required />
              </label>
              <label>
                Password
                <input type="password" name="password" value={form.password} onChange={handleChange} required />
              </label>
              {error && <p className="error">{error}</p>}
              <button className="primary-btn" type="submit" disabled={loading}>
                {loading ? "Signing in..." : "Sign in"}
              </button>
            </form>
            <p className="muted">
              New here? <Link to="/register">Create an account</Link>
            </p>
          </>
        ) : (
          <div className="admin-section">
            <p className="eyebrow">Platform Control</p>
            <h1>Admin Infrastructure.</h1>
            <p className="muted" style={{ marginBottom: "24px" }}>
              Access the core database, manage users, and trigger model retraining.
              Only staff credentials will be accepted here.
            </p>

            <div className="card" style={{ border: "1px solid var(--border)", marginBottom: "24px" }}>
              <h3>Django Administration</h3>
              <p className="muted" style={{ fontSize: "0.9rem", marginTop: "8px" }}>
                Use this portal for exhaustive database management and user permission audits.
              </p>
              <a
                href="http://localhost:8000/admin/"
                target="_blank"
                rel="noopener noreferrer"
                className="secondary-btn"
                style={{ display: "block", textAlign: "center", marginTop: "16px", textDecoration: "none" }}
              >
                Go to Django Admin
              </a>
            </div>

            <div className="card gradient-card">
              <h3>Admin Requirements</h3>
              <p style={{ fontSize: "0.9rem", marginTop: "8px" }}>
                • Must be marked as <strong>is_staff</strong> in DB<br />
                • Passwords must meet complexity standards
              </p>
            </div>

            <button
              className="ghost-btn"
              onClick={() => setMode("user")}
              style={{ width: "100%", marginTop: "24px" }}
            >
              Back to User Login
            </button>
          </div>
        )}
      </div>
      <div className="auth-hero">
        <div className="hero-card">
          <p className="eyebrow">SkillForge AI</p>
          <h2>Turn your resume into a role-ready roadmap.</h2>
          <p>Upload, assess, adapt, and track progress with ML-powered insights.</p>
        </div>
      </div>
    </div>
  );
}
