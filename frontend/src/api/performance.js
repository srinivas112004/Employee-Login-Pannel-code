// src/api/performance.js
const BASE = (process.env.REACT_APP_API_BASE || "http://localhost:8000").replace(/\/$/, "");

function getToken() {
  return (
    localStorage.getItem("access_token") ||
    localStorage.getItem("access") ||
    localStorage.getItem("token") ||
    null
  );
}

function authHeaders(extra = {}) {
  const token = getToken();
  const headers = { Accept: "application/json", ...extra };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

function qs(params = {}) {
  const clean = {};
  Object.keys(params || {}).forEach((k) => {
    const v = params[k];
    if (v !== undefined && v !== null && v !== "") clean[k] = v;
  });
  const s = new URLSearchParams(clean).toString();
  return s ? `?${s}` : "";
}

function buildUrl(path) {
  // If path is absolute, return as-is; else join with BASE
  if (!path) return BASE;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const p = String(path).replace(/^\/+/, "");
  return `${BASE}/${p}`;
}

async function fetchJSON(url, options = {}) {
  console.debug("PERF API >", options.method || "GET", url);
  const res = await fetch(url, options);
  const text = await res.text().catch(() => "");
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text || null;
  }

  if (!res.ok) {
    const err = new Error(data?.detail || data?.message || res.statusText || "Request failed");
    err.status = res.status;
    err.body = data;
    throw err;
  }
  return data;
}

/**
 * Try multiple POST endpoints (useful for backends that expose differently-named action endpoints).
 * paths: array of path strings (absolute or relative to BASE).
 * payload: object to send (will be JSON.stringified)
 * headersExtra: additional headers object (e.g., {"Content-Type": "application/json"})
 *
 * On first successful (res.ok) response returns parsed JSON (or null).
 * If all fail, throws last error (with status & body when available).
 */
async function postWithFallback(paths = [], payload = {}, headersExtra = {}) {
  if (!Array.isArray(paths) || paths.length === 0) {
    throw new Error("No paths provided for postWithFallback");
  }
  let lastErr = null;
  for (const p of paths) {
    const url = buildUrl(p);
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: authHeaders({ "Content-Type": "application/json", ...headersExtra }),
        body: JSON.stringify(payload),
      });
      const text = await res.text().catch(() => "");
      let data = null;
      try {
        data = text ? JSON.parse(text) : null;
      } catch {
        data = text || null;
      }
      if (res.ok) return data;
      const err = new Error(data?.detail || data?.message || res.statusText || "Request failed");
      err.status = res.status;
      err.body = data;
      lastErr = err;
      // if 400 with body, return that error (but continue trying other paths)
    } catch (fetchErr) {
      lastErr = fetchErr;
    }
  }
  if (lastErr) throw lastErr;
  throw new Error("All POST paths failed");
}

/* -------------------------
   Categories
   ------------------------- */
export async function listCategories(params = {}) {
  return fetchJSON(buildUrl(`api/performance/categories/${qs(params)}`), {
    headers: authHeaders(),
  });
}

export async function createCategory(payload) {
  return fetchJSON(buildUrl(`api/performance/categories/`), {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function updateCategory(id, payload) {
  return fetchJSON(buildUrl(`api/performance/categories/${id}/`), {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function deleteCategory(id) {
  return fetchJSON(buildUrl(`api/performance/categories/${id}/`), {
    method: "DELETE",
    headers: authHeaders(),
  });
}

/* -------------------------
   Goals / OKRs
   ------------------------- */
export async function listGoals(params = {}) {
  return fetchJSON(buildUrl(`api/performance/goals/${qs(params)}`), {
    headers: authHeaders(),
  });
}

export async function getGoal(id) {
  return fetchJSON(buildUrl(`api/performance/goals/${id}/`), {
    headers: authHeaders(),
  });
}

export async function createGoal(payload) {
  return fetchJSON(buildUrl(`api/performance/goals/`), {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function patchGoal(id, patch) {
  return fetchJSON(buildUrl(`api/performance/goals/${id}/`), {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(patch),
  });
}

export async function deleteGoal(id) {
  return fetchJSON(buildUrl(`api/performance/goals/${id}/`), {
    method: "DELETE",
    headers: authHeaders(),
  });
}

export async function myGoals() {
  return fetchJSON(buildUrl(`api/performance/goals/my-goals/`), {
    headers: authHeaders(),
  });
}

export async function teamGoals() {
  return fetchJSON(buildUrl(`api/performance/goals/team-goals/`), {
    headers: authHeaders(),
  });
}

/**
 * updateGoalProgress: try canonical endpoint first, then alternate action names / collection endpoints.
 * Keeps same signature.
 */
export async function updateGoalProgress(goalId, payload) {
  const candidates = [
    `api/performance/goals/${goalId}/update-progress/`,
    `api/performance/goals/${goalId}/update_progress/`,
    `api/performance/goals/${goalId}/progress/`,
    `api/performance/goals/${goalId}/updates/`,
    `api/performance/goals/${goalId}/add-progress/`,
  ];
  return postWithFallback(candidates, payload);
}

/**
 * completeGoal: try different possible endpoints for marking complete.
 */
export async function completeGoal(goalId, payload = {}) {
  const candidates = [
    `api/performance/goals/${goalId}/complete/`,
    `api/performance/goals/${goalId}/mark-complete/`,
    `api/performance/goals/${goalId}/complete_goal/`,
    `api/performance/goals/${goalId}/complete/`, // duplicate intentionally harmless
  ];
  return postWithFallback(candidates, payload);
}

/**
 * addMilestoneToGoal: fallback to collection create if action endpoint is not present
 */
export async function addMilestoneToGoal(goalId, payload) {
  const candidates = [
    `api/performance/goals/${goalId}/add-milestone/`,
    `api/performance/goals/${goalId}/milestones/`,
    `api/performance/milestones/`, // some APIs accept goal in payload
  ];
  // if using the last candidate we should include goal reference if not present
  if (!payload.goal) {
    payload = { ...payload, goal: goalId };
  }
  return postWithFallback(candidates, payload);
}

/**
 * addGoalComment: fallbacks
 */
export async function addGoalComment(goalId, payload) {
  const candidates = [
    `api/performance/goals/${goalId}/add-comment/`,
    `api/performance/goals/${goalId}/add_comment/`,
    `api/performance/goals/${goalId}/comments/`,
    `api/performance/comments/`, // accept goal in payload
  ];
  if (!payload.goal) payload = { ...payload, goal: goalId };
  return postWithFallback(candidates, payload);
}

export async function goalComments(goalId, params = {}) {
  return fetchJSON(buildUrl(`api/performance/goals/${goalId}/comments/${qs(params)}`), {
    headers: authHeaders(),
  });
}

export async function overdueGoals(params = {}) {
  return fetchJSON(buildUrl(`api/performance/goals/overdue/${qs(params)}`), {
    headers: authHeaders(),
  });
}

export async function goalDashboard() {
  return fetchJSON(buildUrl(`api/performance/goals/dashboard/`), {
    headers: authHeaders(),
  });
}

/* -------------------------
   Milestones
   ------------------------- */
export async function listMilestones(params = {}) {
  return fetchJSON(buildUrl(`api/performance/milestones/${qs(params)}`), {
    headers: authHeaders(),
  });
}

export async function createMilestone(payload) {
  return fetchJSON(buildUrl(`api/performance/milestones/`), {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function patchMilestone(id, patch) {
  return fetchJSON(buildUrl(`api/performance/milestones/${id}/`), {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(patch),
  });
}

export async function deleteMilestone(id) {
  return fetchJSON(buildUrl(`api/performance/milestones/${id}/`), {
    method: "DELETE",
    headers: authHeaders(),
  });
}

export async function completeMilestone(id) {
  return fetchJSON(buildUrl(`api/performance/milestones/${id}/complete/`), {
    method: "POST",
    headers: authHeaders(),
  });
}

/* -------------------------
   KPIs
   ------------------------- */
export async function listKpis(params = {}) {
  return fetchJSON(buildUrl(`api/performance/kpis/${qs(params)}`), {
    headers: authHeaders(),
  });
}

/**
 * createKpi: try canonical endpoint and fallbacks (collection vs action)
 * Keep same signature.
 */
export async function createKpi(payload) {
  const candidates = [
    `api/performance/kpis/`,
    `api/performance/kpis/create/`,
    `api/performance/kpi/`,
    `api/performance/kpis/add/`,
  ];
  return postWithFallback(candidates, payload);
}

export async function patchKpi(id, patch) {
  return fetchJSON(buildUrl(`api/performance/kpis/${id}/`), {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(patch),
  });
}

/**
 * updateKpiValue: sometimes implemented as action or collection
 */
export async function updateKpiValue(id, payload) {
  const candidates = [
    `api/performance/kpis/${id}/update-value/`,
    `api/performance/kpis/${id}/update_value/`,
    `api/performance/kpis/${id}/update/`,
    `api/performance/kpis/${id}/value/`,
  ];
  return postWithFallback(candidates, payload);
}

export async function kpiDashboard() {
  return fetchJSON(buildUrl(`api/performance/kpis/kpi-dashboard/`), {
    headers: authHeaders(),
  });
}

/* -------------------------
   Progress updates feed
   ------------------------- */
export async function progressUpdates(params = {}) {
  return fetchJSON(buildUrl(`api/performance/progress-updates/${qs(params)}`), {
    headers: authHeaders(),
  });
}

/* -------------------------
   Default export (convenience)
   ------------------------- */
export default {
  // categories
  listCategories,
  createCategory,
  updateCategory,
  deleteCategory,

  // goals
  listGoals,
  getGoal,
  createGoal,
  patchGoal,
  deleteGoal,
  myGoals,
  teamGoals,
  updateGoalProgress,
  completeGoal,
  addMilestoneToGoal,
  addGoalComment,
  goalComments,
  overdueGoals,
  goalDashboard,

  // milestones
  listMilestones,
  createMilestone,
  patchMilestone,
  deleteMilestone,
  completeMilestone,

  // kpis
  listKpis,
  createKpi,
  patchKpi,
  updateKpiValue,
  kpiDashboard,

  // progress
  progressUpdates,
};
