// src/api/hrapi.js
// Robust axios instance + HR API helpers
// Place at src/api/hrapi.js

import axios from "axios";

/**
 * baseURL: keep without trailing /api since endpoints include /api prefix
 * If you prefer baseURL with /api instead, remove "/api" prefixes in endpoints below.
 */

const API = axios.create({
  baseURL: process.env.REACT_APP_API_BASE || "http://localhost:8000",
  timeout: 60000,
  withCredentials: false,
});

/**
 * Interceptor:
 * - Reads tokens from localStorage keys: "access_token", "token", "access", "authToken", "token_data"
 * - Supports raw token string, JSON string with {access, token}, or already-prefixed strings ("Bearer ...", "Token ...")
 * - Attaches Authorization header as "Bearer <token>" by default (change to Token if backend needs)
 */
API.interceptors.request.use(
  (config) => {
    try {
      const maybeToken =
        localStorage.getItem("access_token") ||
        localStorage.getItem("token") ||
        localStorage.getItem("access") ||
        localStorage.getItem("authToken") ||
        localStorage.getItem("token_data") ||
        null;

      if (!maybeToken) return config;

      let token = maybeToken;

      // parse JSON-like string to pick access/token field
      if (typeof maybeToken === "string") {
        const trimmed = maybeToken.trim();
        if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
          try {
            const parsed = JSON.parse(trimmed);
            token = parsed?.access || parsed?.token || parsed?.auth || token;
          } catch (e) {
            // not JSON — keep raw
          }
        }
      }

      if (typeof token === "string") {
        const t = token.trim();
        // if already prefixed, use as-is
        if (t.toLowerCase().startsWith("bearer ") || t.toLowerCase().startsWith("token ")) {
          config.headers = config.headers || {};
          config.headers.Authorization = t;
          return config;
        }
        // otherwise attach as Bearer by default
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${t}`;
      }
    } catch (e) {
      // silent: do not break requests
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/* -------------------- Employees API -------------------- */
export const fetchMyProfile = () => API.get("/api/hr/employees/my_profile/");
export const fetchEmployees = (params = {}) => API.get("/api/hr/employees/", { params });
export const getEmployee = (id) => API.get(`/api/hr/employees/${id}/`);
export const createEmployee = (payload) => API.post("/api/hr/employees/", payload);
export const updateEmployee = (id, payload) => API.patch(`/api/hr/employees/${id}/`, payload);
export const deleteEmployee = (id) => API.delete(`/api/hr/employees/${id}/`);

/* -------------------- Documents -------------------- */
export const fetchDocuments = (params = {}) => API.get("/api/hr/documents/", { params });
export const uploadDocument = (formData, onUploadProgress) =>
  API.post("/api/hr/documents/", formData, {
    onUploadProgress: (ev) => {
      if (typeof onUploadProgress === "function") {
        const pct = ev.total ? Math.round((ev.loaded * 100) / ev.total) : 0;
        onUploadProgress(pct);
      }
    },
  });
export const deleteDocument = (id) => API.delete(`/api/hr/documents/${id}/`);
export const verifyDocument = (id) => API.post(`/api/hr/documents/${id}/verify/`);

/* -------------------- Onboarding -------------------- */
export const fetchOnboardingTasks = (params = {}) => API.get("/api/hr/onboarding/", { params });
export const createOnboardingTask = (payload) => API.post("/api/hr/onboarding/", payload);
export const updateOnboardingTask = (id, payload) => API.patch(`/api/hr/onboarding/${id}/`, payload);
export const deleteOnboardingTask = (id) => API.delete(`/api/hr/onboarding/${id}/`);
export const completeOnboardingTask = (id, payload = {}) => API.post(`/api/hr/onboarding/${id}/complete/`, payload);
export const completeProfileOnboarding = (employeeId) => API.post(`/api/hr/employees/${employeeId}/complete_onboarding/`);

/* -------------------- Employment History -------------------- */
export const fetchEmploymentHistory = (params = {}) => API.get("/api/hr/employment-history/", { params });
export const getEmploymentRecord = (id) => API.get(`/api/hr/employment-history/${id}/`);
export const createEmploymentHistory = (formData, onUploadProgress) =>
  API.post("/api/hr/employment-history/", formData, {
    onUploadProgress: (ev) => {
      if (typeof onUploadProgress === "function") {
        const pct = ev.total ? Math.round((ev.loaded * 100) / ev.total) : 0;
        onUploadProgress(pct);
      }
    },
  });
export const updateEmploymentHistory = (id, payload) => API.patch(`/api/hr/employment-history/${id}/`, payload);
export const deleteEmploymentHistory = (id) => API.delete(`/api/hr/employment-history/${id}/`);

/* -------------------- Exports -------------------- */
const HRApi = {
  fetchMyProfile,
  fetchEmployees,
  getEmployee,
  createEmployee,
  updateEmployee,
  deleteEmployee,

  fetchDocuments,
  uploadDocument,
  deleteDocument,
  verifyDocument,

  fetchOnboardingTasks,
  createOnboardingTask,
  updateOnboardingTask,
  deleteOnboardingTask,
  completeOnboardingTask,
  completeProfileOnboarding,

  fetchEmploymentHistory,
  getEmploymentRecord,
  createEmploymentHistory,
  updateEmploymentHistory,
  deleteEmploymentHistory,

  // expose raw instance if needed
  __axios: API,
};

export default HRApi;
