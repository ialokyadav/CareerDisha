import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { api, setToken } from "../api/client.js";

const DJANGO_ADMIN_URL = import.meta.env.VITE_DJANGO_ADMIN_URL || "http://127.0.0.1:8000/admin/";

export default function Login() {
  const [form, setForm] = useState({ username: "", password: "" });
  const [resetForm, setResetForm] = useState({
    username: "",
    email: "",
    otp: "",
    new_password: "",
    confirm_password: "",
  });
  const [error, setError] = useState("");
  const [resetError, setResetError] = useState("");
  const [resetMessage, setResetMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
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
      try {
        const profile = await api.profile();
        const isAdmin = profile?.is_staff || profile?.role === "Admin";
        if (mode === "admin") {
          if (isAdmin) {
            window.location.href = DJANGO_ADMIN_URL;
            return;
          }
          setError("This account is not an admin account.");
          return;
        }
      } catch (_err) {
        // Fallback to regular app if profile check fails.
      }
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResetChange = (event) => {
    setResetForm({ ...resetForm, [event.target.name]: event.target.value });
  };

  const handleRequestOtp = async (event) => {
    event.preventDefault();
    setResetError("");
    setResetMessage("");
    setResetLoading(true);
    try {
      const data = await api.forgotPasswordRequestOtp({
        username: resetForm.username,
        email: resetForm.email,
      });
      setOtpSent(true);
      setResetMessage(data?.message || "OTP sent to your email.");
    } catch (err) {
      setResetError(err.message);
    } finally {
      setResetLoading(false);
    }
  };

  const handleVerifyOtpAndResetPassword = async (event) => {
    event.preventDefault();
    setResetError("");
    setResetMessage("");
    setResetLoading(true);
    try {
      const data = await api.forgotPasswordVerifyOtp(resetForm);
      setResetMessage(data?.message || "Password updated successfully. Please sign in.");
      setShowForgotPassword(false);
      setOtpSent(false);
      setResetForm({
        username: "",
        email: "",
        otp: "",
        new_password: "",
        confirm_password: "",
      });
    } catch (err) {
      setResetError(err.message);
    } finally {
      setResetLoading(false);
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
            <button
              type="button"
              className="forgot-password-btn"
              onClick={() => {
                setError("");
                setResetError("");
                setResetMessage("");
                setOtpSent(false);
                setShowForgotPassword((prev) => !prev);
              }}
            >
              {showForgotPassword ? "Back to login" : "Forgot password?"}
            </button>
            {showForgotPassword && (
              <>
                {!otpSent ? (
                  <form className="form" onSubmit={handleRequestOtp} style={{ marginTop: "12px" }}>
                    <label>
                      Username
                      <input
                        name="username"
                        value={resetForm.username}
                        onChange={handleResetChange}
                        required
                      />
                    </label>
                    <label>
                      Registered email
                      <input
                        type="email"
                        name="email"
                        value={resetForm.email}
                        onChange={handleResetChange}
                        required
                      />
                    </label>
                    {resetError && <p className="error">{resetError}</p>}
                    <button className="secondary-btn" type="submit" disabled={resetLoading}>
                      {resetLoading ? "Sending OTP..." : "Send OTP"}
                    </button>
                  </form>
                ) : (
                  <form className="form" onSubmit={handleVerifyOtpAndResetPassword} style={{ marginTop: "12px" }}>
                    <label>
                      OTP
                      <input
                        name="otp"
                        value={resetForm.otp}
                        onChange={handleResetChange}
                        inputMode="numeric"
                        pattern="[0-9]{6}"
                        placeholder="Enter 6-digit OTP"
                        required
                      />
                    </label>
                    <label>
                      New password
                      <input
                        type="password"
                        name="new_password"
                        value={resetForm.new_password}
                        onChange={handleResetChange}
                        required
                      />
                    </label>
                    <label>
                      Confirm new password
                      <input
                        type="password"
                        name="confirm_password"
                        value={resetForm.confirm_password}
                        onChange={handleResetChange}
                        required
                      />
                    </label>
                    {resetError && <p className="error">{resetError}</p>}
                    <button className="secondary-btn" type="submit" disabled={resetLoading}>
                      {resetLoading ? "Verifying..." : "Verify OTP & Reset Password"}
                    </button>
                    <button
                      type="button"
                      className="forgot-password-btn"
                      onClick={handleRequestOtp}
                      disabled={resetLoading}
                    >
                      {resetLoading ? "Sending..." : "Resend OTP"}
                    </button>
                  </form>
                )}
              </>
            )}
            {resetMessage && <p className="muted">{resetMessage}</p>}
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
          <img
            src="/logo.png"
            alt="CareerDisha AI logo"
            className="brand-logo"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
          <p className="eyebrow">CareerDisha AI</p>
          <h2>Turn your resume into a role-ready roadmap.</h2>
          <p>Upload, assess, adapt, and track progress with ML-powered insights.</p>
        </div>
      </div>
    </div>
  );
}
