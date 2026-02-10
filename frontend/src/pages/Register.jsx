import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client.js";

export default function Register() {
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    role: "Student"
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (event) => {
    setForm({ ...form, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.register(form);
      navigate("/login");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-layout">
      <div className="auth-panel">
        <p className="eyebrow">Start here</p>
        <h1>Build your skill passport.</h1>
        <p className="muted">Create an account to unlock adaptive testing.</p>
        <form className="form" onSubmit={handleSubmit}>
          <label>
            Username
            <input name="username" value={form.username} onChange={handleChange} required />
          </label>
          <label>
            Email
            <input type="email" name="email" value={form.email} onChange={handleChange} required />
          </label>
          <label>
            Password
            <input type="password" name="password" value={form.password} onChange={handleChange} required />
          </label>
          <div className="grid-2">
            <label>
              First name
              <input name="first_name" value={form.first_name} onChange={handleChange} />
            </label>
            <label>
              Last name
              <input name="last_name" value={form.last_name} onChange={handleChange} />
            </label>
          </div>
          <label>
            Role
            <select name="role" value={form.role} onChange={handleChange}>
              <option value="Student">Student</option>
              <option value="Admin">Admin</option>
            </select>
          </label>
          {error && <p className="error">{error}</p>}
          <button className="primary-btn" type="submit" disabled={loading}>
            {loading ? "Creating..." : "Create account"}
          </button>
        </form>
        <p className="muted">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
      <div className="auth-hero alt">
        <div className="hero-card">
          <p className="eyebrow">Role-first learning</p>
          <h2>Personalized roadmaps, adaptive practice, clear progress.</h2>
          <p>Join thousands of learners shaping their placement-ready skills.</p>
        </div>
      </div>
    </div>
  );
}
