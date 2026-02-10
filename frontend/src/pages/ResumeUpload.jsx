import React, { useState, useEffect } from "react";
import SectionHeader from "../components/SectionHeader.jsx";
import { api } from "../api/client.js";

export default function ResumeUpload() {
  const [file, setFile] = useState(null);
  const [manualText, setManualText] = useState("");
  const [manualForm, setManualForm] = useState({
    name: "",
    email: "",
    phone: "",
    education: "",
    skills: "",
    experience: "",
    projects: "",
    certifications: ""
  });
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [targetRole, setTargetRole] = useState("");
  const [roles, setRoles] = useState([]);
  const [inputMode, setInputMode] = useState("file"); // 'file', 'text', 'form'

  useEffect(() => {
    api.listRoles()
      .then(data => {
        setRoles(data.roles);
        if (data.roles.length > 0) {
          setTargetRole(data.roles[0]);
        }
      })
      .catch(err => console.error("Failed to load roles:", err));
  }, []);

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a resume file.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      if (targetRole) {
        formData.append("selected_role", targetRole);
      }
      const data = await api.uploadResume(formData);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleManual = async () => {
    if (!manualText.trim()) {
      setError("Please paste your resume text.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const data = await api.manualResume({ text: manualText, selected_role: targetRole });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFormChange = (event) => {
    setManualForm({ ...manualForm, [event.target.name]: event.target.value });
  };

  const buildManualText = () => {
    return `Name: ${manualForm.name}\nEmail: ${manualForm.email}\nPhone: ${manualForm.phone}\n\nEducation:\n${manualForm.education}\n\nSkills:\n${manualForm.skills}\n\nExperience:\n${manualForm.experience}\n\nProjects:\n${manualForm.projects}\n\nCertifications:\n${manualForm.certifications}`.trim();
  };

  const handleManualForm = async () => {
    if (!manualForm.name && !manualForm.skills && !manualForm.experience) {
      setError("Please fill at least Name, Skills, or Experience.");
      return;
    }
    const composed = buildManualText();
    setManualText(composed);
    setError("");
    setLoading(true);
    try {
      const data = await api.manualResume({ text: composed, selected_role: targetRole });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Resume intake"
        title="Upload your resume for skill extraction"
        subtitle="PDF, DOCX, and TXT supported."
      />
      <div className="tab-row">
        <button
          className={`tab-btn ${inputMode === "file" ? "active" : ""}`}
          onClick={() => setInputMode("file")}
        >
          Upload file
        </button>
        <button
          className={`tab-btn ${inputMode === "text" ? "active" : ""}`}
          onClick={() => setInputMode("text")}
        >
          Paste text
        </button>
        <button
          className={`tab-btn ${inputMode === "form" ? "active" : ""}`}
          onClick={() => setInputMode("form")}
        >
          Fill form
        </button>
      </div>

      <div className="card">
        <label>
          Target role (optional)
          <select value={targetRole} onChange={(e) => setTargetRole(e.target.value)}>
            <option value="">-- No target role --</option>
            {roles.map((role) => (
              <option key={role} value={role}>{role}</option>
            ))}
          </select>
        </label>
      </div>

      {inputMode === "file" && (
        <div className="card">
          <input type="file" onChange={(e) => setFile(e.target.files[0])} />
          <button className="primary-btn" onClick={handleUpload} disabled={loading}>
            {loading ? "Processing..." : "Upload & Extract"}
          </button>
        </div>
      )}

      {inputMode === "text" && (
        <div className="card">
          <label>
            Or paste resume text
            <textarea
              rows="8"
              value={manualText}
              onChange={(e) => setManualText(e.target.value)}
              placeholder="Paste your resume content here..."
            />
          </label>
          <button className="primary-btn" onClick={handleManual} disabled={loading}>
            {loading ? "Processing..." : "Analyze Manual Resume"}
          </button>
          {error && <p className="error">{error}</p>}
        </div>
      )}

      {inputMode === "form" && (
        <div className="card">
          <h3>Manual resume form</h3>
          <div className="grid-2">
            <label>
              Name
              <input name="name" value={manualForm.name} onChange={handleFormChange} />
            </label>
            <label>
              Email
              <input name="email" value={manualForm.email} onChange={handleFormChange} />
            </label>
            <label>
              Phone
              <input name="phone" value={manualForm.phone} onChange={handleFormChange} />
            </label>
            <label>
              Skills (comma-separated)
              <input name="skills" value={manualForm.skills} onChange={handleFormChange} />
            </label>
          </div>
          <label>
            Education
            <textarea name="education" rows="4" value={manualForm.education} onChange={handleFormChange} />
          </label>
          <label>
            Experience
            <textarea name="experience" rows="4" value={manualForm.experience} onChange={handleFormChange} />
          </label>
          <label>
            Projects
            <textarea name="projects" rows="4" value={manualForm.projects} onChange={handleFormChange} />
          </label>
          <label>
            Certifications
            <textarea name="certifications" rows="3" value={manualForm.certifications} onChange={handleFormChange} />
          </label>
          <button className="primary-btn" onClick={handleManualForm} disabled={loading}>
            {loading ? "Processing..." : "Generate & Analyze"}
          </button>
          {error && <p className="error">{error}</p>}
        </div>
      )}
      {result && (
        <>
          <div className="card gradient-card">
            <div className="grid-2">
              <div>
                <p className="eyebrow">Contact Information</p>
                <h3 className="big" style={{ margin: "4px 0" }}>{result.contact?.email || "Email not found"}</h3>
                <p className="muted">{result.contact?.phone || "Phone not found"}</p>
              </div>
              <div style={{ textAlign: "right" }}>
                <p className="eyebrow">Institution</p>
                <h3 className="big" style={{ margin: "4px 0" }}>{result.education?.college || "Not found"}</h3>
                <p className="pill primary">{result.education?.higher_education || "Degree not found"}</p>
              </div>
            </div>
          </div>

          {result.prediction && (
            <div className="card" style={{ borderLeft: "4px solid var(--primary)", padding: "16px 24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <p className="eyebrow">Predicted Candidate Role</p>
                  <h3 style={{ margin: "4px 0", color: "var(--primary)" }}>{result.prediction.role}</h3>
                </div>
                <div style={{ textAlign: "right" }}>
                  <p className="eyebrow">Confidence / Signal</p>
                  <p className="big" style={{ margin: 0 }}>{(result.prediction.confidence * 100).toFixed(0)}%</p>
                </div>
              </div>
              {result.prediction.matched_skills?.length > 0 && (
                <div style={{ marginTop: "12px" }}>
                  <p className="muted" style={{ fontSize: "0.85rem" }}>
                    <strong>{result.prediction.matched_skills.length} skills</strong> matched this role.
                  </p>
                </div>
              )}
            </div>
          )}

          <div className="card">
            <h3>Extracted Skills</h3>
            <ul style={{
              marginTop: "16px",
              columns: "2",
              listStyleType: "none",
              padding: 0
            }}>
              {result.skills.map((skill) => (
                <li key={skill.skill} style={{
                  padding: "8px 0",
                  borderBottom: "1px solid var(--border)",
                  display: "flex",
                  alignItems: "center"
                }}>
                  <span style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: "var(--primary)",
                    marginRight: "12px"
                  }}></span>
                  {skill.skill}
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
