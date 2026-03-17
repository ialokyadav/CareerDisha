
import React, { useState } from "react";
import { Link } from "react-router-dom";
import { api, setToken } from "../api/client.js";

export default function LoginPopup({ isOpen, onClose, onLoginSuccess }) {
    if (!isOpen) return null;

    const [form, setForm] = useState({ username: "", password: "" });
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

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
            if (onLoginSuccess) {
                onLoginSuccess();
            } else {
                onClose();
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <button className="modal-close" onClick={onClose}>×</button>

                <div style={{ textAlign: "center", marginBottom: "24px" }}>
                    <p className="eyebrow">Sign in required</p>
                    <h2 style={{ fontSize: "1.8rem" }}>Login to Upload</h2>
                    <p className="muted">You need to be logged in to analyze resumes.</p>
                </div>

                <form className="form" onSubmit={handleSubmit}>
                    <label>
                        Username
                        <input
                            name="username"
                            value={form.username}
                            onChange={handleChange}
                            required
                            autoFocus
                        />
                    </label>
                    <label>
                        Password
                        <input
                            type="password"
                            name="password"
                            value={form.password}
                            onChange={handleChange}
                            required
                        />
                    </label>

                    {error && <p className="error" style={{ fontSize: "0.9rem" }}>{error}</p>}

                    <button className="primary-btn" type="submit" disabled={loading} style={{ width: "100%", marginTop: "8px" }}>
                        {loading ? "Signing in..." : "Sign in & Continue"}
                    </button>
                </form>

                <div style={{ marginTop: "24px", textAlign: "center", fontSize: "0.9rem" }}>
                    <p className="muted">
                        Don't have an account? <Link to="/register" onClick={onClose} style={{ color: "var(--primary)", fontWeight: "600" }}>Sign up</Link>
                    </p>
                </div>
            </div>
        </div>
    );
}
