import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Shell from "./components/Shell.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import ResumeUpload from "./pages/ResumeUpload.jsx";
import RolePrediction from "./pages/RolePrediction.jsx";
import SkillGap from "./pages/SkillGap.jsx";
import Roadmap from "./pages/Roadmap.jsx";
import TestCenter from "./pages/TestCenter.jsx";
import Analytics from "./pages/Analytics.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";

export default function App() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/resume" element={<ResumeUpload />} />
        <Route path="/role" element={<RolePrediction />} />
        <Route path="/skill-gap" element={<SkillGap />} />
        <Route path="/roadmap" element={<Roadmap />} />
        <Route path="/tests" element={<TestCenter />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/admin" element={<AdminDashboard />} />
      </Routes>
    </Shell>
  );
}
