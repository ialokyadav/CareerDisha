const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export function getToken() {
  return localStorage.getItem("jwt_token");
}

export function setToken(token) {
  localStorage.setItem("jwt_token", token);
}

export function clearToken() {
  localStorage.removeItem("jwt_token");
}

async function request(path, options = {}) {
  const headers = { ...options.headers };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers
  });

  const contentType = response.headers.get("content-type");
  const data = contentType && contentType.includes("application/json")
    ? await response.json()
    : null;

  if (!response.ok) {
    if (response.status === 401) {
      clearToken();
      const message = data?.detail || data?.error || "Session expired. Please login again.";
      if (message.toLowerCase().includes("token") && message.toLowerCase().includes("not valid")) {
        throw new Error("Given token is not valid. Please login again.");
      }
      throw new Error(message);
    }
    const message = data?.error || data?.detail || "Request failed";
    throw new Error(message);
  }

  return data;
}

export const api = {
  register: (payload) => request("/api/auth/register/", { method: "POST", body: JSON.stringify(payload) }),
  login: (payload) => request("/api/auth/token/", { method: "POST", body: JSON.stringify(payload) }),
  profile: () => request("/api/auth/profile/"),
  uploadResume: (formData) => request("/api/resumes/upload/", { method: "POST", body: formData }),
  manualResume: (payload) => request("/api/resumes/manual-text/", { method: "POST", body: JSON.stringify(payload) }),
  predictRole: (payload) => request("/api/resumes/predict-role/", { method: "POST", body: JSON.stringify(payload) }),
  skillGap: (payload) => request("/api/resumes/skill-gap/", { method: "POST", body: JSON.stringify(payload) }),
  generateTest: (payload) => request("/api/assessments/generate/", { method: "POST", body: JSON.stringify(payload) }),
  submitTest: (payload) => request("/api/assessments/submit/", { method: "POST", body: JSON.stringify(payload) }),
  performanceHistory: () => request("/api/analytics/history/"),
  performanceSummary: () => request("/api/analytics/summary/"),
  listRoles: () => request("/api/assessments/roles/"),
  generateRoadmap: (payload) => request("/api/roadmap/generate/", { method: "POST", body: JSON.stringify(payload) }),
  getLatestExtraction: () => request("/api/resumes/latest-extraction/"),
  getTrainingStatus: () => request("/api/resumes/training-status/"),
  addManualTrainingData: (payload) => request("/api/resumes/add-manual-data/", { method: "POST", body: JSON.stringify(payload) }),
  triggerRetraining: () => request("/api/resumes/admin-retrain/", { method: "POST" })
};
