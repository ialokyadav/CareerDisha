import React from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import { clearToken, getToken } from "../api/client.js";

const navItems = [
  { path: "/dashboard", label: "Dashboard" },
  { path: "/resume", label: "Resume" },
  { path: "/role", label: "Role Match" },
  { path: "/skill-gap", label: "Skill Gap" },
  { path: "/roadmap", label: "Roadmap" },
  { path: "/tests", label: "Tests" },
  { path: "/analytics", label: "Analytics" }
];

export default function Shell({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const token = getToken();
  const showNav = !["/login", "/register"].includes(location.pathname);

  const handleLogout = () => {
    clearToken();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      {showNav && (
        <aside className="sidebar">
          <div className="logo-block">
            <div className="logo-mark">
              <img
                src="/logo.png"
                alt="CareerDisha AI logo"
                className="logo-mark-img"
                onError={(e) => {
                  e.currentTarget.style.display = "none";
                  const fallback = e.currentTarget.parentElement?.querySelector(".logo-mark-fallback");
                  if (fallback) fallback.style.display = "grid";
                }}
              />
              <span className="logo-mark-fallback">CD</span>
            </div>
            <div>
              <p className="logo-title">CareerDisha AI</p>
              <p className="logo-sub">Adaptive Assessment</p>
            </div>
          </div>
          <nav className="nav-links">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `nav-link ${isActive ? "active" : ""}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="auth-actions" style={{ marginTop: "auto", padding: "16px 0" }}>
            {token ? (
              <button className="ghost-btn" onClick={handleLogout} style={{ width: "100%" }}>
                Sign out
              </button>
            ) : (
              <>
                <NavLink to="/login" className="nav-link">Login</NavLink>
                <NavLink to="/register" className="nav-link">Sign up</NavLink>
              </>
            )}
          </div>
        </aside>
      )}
      <main className={showNav ? "main-content" : "main-content full"}>
        {children}
      </main>
    </div>
  );
}
