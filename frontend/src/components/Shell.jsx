import React from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import { clearToken, getToken, api } from "../api/client.js";

const navItems = [
  { path: "/dashboard", label: "Dashboard" },
  { path: "/resume", label: "Resume" },
  { path: "/role", label: "Role Match" },
  { path: "/skill-gap", label: "Skill Gap" },
  { path: "/roadmap", label: "Roadmap" },
  { path: "/tests", label: "Tests" },
  { path: "/analytics", label: "Analytics" }
];

const adminNavItem = { path: "/admin", label: "Admin" };

export default function Shell({ children }) {
  const navigate = useNavigate();
  const location = useLocation();
  const token = getToken();
  const [isAdmin, setIsAdmin] = React.useState(false);
  const showNav = !["/login", "/register"].includes(location.pathname);

  React.useEffect(() => {
    if (token) {
      api.profile().then(profile => {
        setIsAdmin(profile.is_staff || profile.role === "Admin");
      }).catch(() => { });
    }
  }, [token]);

  const handleLogout = () => {
    clearToken();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      {showNav && (
        <aside className="sidebar">
          <div className="logo-block">
            <div className="logo-mark">SF</div>
            <div>
              <p className="logo-title">SkillForge AI</p>
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
            {isAdmin && (
              <NavLink
                key={adminNavItem.path}
                to={adminNavItem.path}
                className={({ isActive }) =>
                  `nav-link ${isActive ? "active" : ""}`
                }
                style={{ borderTop: "1px solid rgba(255,255,255,0.05)", marginTop: "8px", paddingTop: "16px" }}
              >
                {adminNavItem.label}
              </NavLink>
            )}
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
