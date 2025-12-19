// src/api/reviews.js
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

async function fetchJSON(url, options = {}) {
  console.debug("REV API >", options.method || "GET", url);
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

/* -------------------------
   Review Cycles
   ------------------------- */
export async function listReviewCycles(params = {}) {
  return fetchJSON(`${BASE}/api/reviews/review-cycles/${qs(params)}`, {
    headers: authHeaders(),
  });
}

export async function getReviewCycle(id) {
  return fetchJSON(`${BASE}/api/reviews/review-cycles/${id}/`, {
    headers: authHeaders(),
  });
}

export async function createReviewCycle(payload) {
  return fetchJSON(`${BASE}/api/reviews/review-cycles/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function updateReviewCycle(id, payload) {
  return fetchJSON(`${BASE}/api/reviews/review-cycles/${id}/`, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function patchReviewCycle(id, patch) {
  return fetchJSON(`${BASE}/api/reviews/review-cycles/${id}/`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(patch),
  });
}

export async function deleteReviewCycle(id) {
  return fetchJSON(`${BASE}/api/reviews/review-cycles/${id}/`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}

export async function activateReviewCycle(id) {
  return fetchJSON(`${BASE}/api/reviews/review-cycles/${id}/activate/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
  });
}

export async function completeReviewCycle(id) {
  return fetchJSON(`${BASE}/api/reviews/review-cycles/${id}/complete/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
  });
}

export async function getCycleStatistics(id) {
  return fetchJSON(`${BASE}/api/reviews/review-cycles/${id}/statistics/`, {
    headers: authHeaders(),
  });
}

/* -------------------------
   Reviews
   ------------------------- */
export async function listReviews(params = {}) {
  return fetchJSON(`${BASE}/api/reviews/reviews/${qs(params)}`, {
    headers: authHeaders(),
  });
}

export async function getReview(id) {
  return fetchJSON(`${BASE}/api/reviews/reviews/${id}/`, {
    headers: authHeaders(),
  });
}

export async function createReview(payload) {
  return fetchJSON(`${BASE}/api/reviews/reviews/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function patchReview(id, patch) {
  return fetchJSON(`${BASE}/api/reviews/reviews/${id}/`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(patch),
  });
}

export async function deleteReview(id) {
  return fetchJSON(`${BASE}/api/reviews/reviews/${id}/`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}

export async function calculateRating(reviewId, payload = {}) {
  return fetchJSON(`${BASE}/api/reviews/reviews/${reviewId}/calculate_rating/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function myReviews(params = {}) {
  return fetchJSON(`${BASE}/api/reviews/reviews/my_reviews/${qs(params)}`, {
    headers: authHeaders(),
  });
}

export async function pendingReviews(params = {}) {
  return fetchJSON(`${BASE}/api/reviews/reviews/pending_reviews/${qs(params)}`, {
    headers: authHeaders(),
  });
}

/* -------------------------
   Self-Assessments
   ------------------------- */
export async function listSelfAssessments(params = {}) {
  return fetchJSON(`${BASE}/api/reviews/self-assessments/${qs(params)}`, {
    headers: authHeaders(),
  });
}

export async function getSelfAssessment(id) {
  return fetchJSON(`${BASE}/api/reviews/self-assessments/${id}/`, {
    headers: authHeaders(),
  });
}

export async function createSelfAssessment(payload) {
  return fetchJSON(`${BASE}/api/reviews/self-assessments/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function patchSelfAssessment(id, patch) {
  return fetchJSON(`${BASE}/api/reviews/self-assessments/${id}/`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(patch),
  });
}

export async function deleteSelfAssessment(id) {
  return fetchJSON(`${BASE}/api/reviews/self-assessments/${id}/`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}

/* -------------------------
   Manager Reviews
   ------------------------- */
export async function listManagerReviews(params = {}) {
  return fetchJSON(`${BASE}/api/reviews/manager-reviews/${qs(params)}`, {
    headers: authHeaders(),
  });
}

export async function getManagerReview(id) {
  return fetchJSON(`${BASE}/api/reviews/manager-reviews/${id}/`, {
    headers: authHeaders(),
  });
}

export async function createManagerReview(payload) {
  return fetchJSON(`${BASE}/api/reviews/manager-reviews/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function patchManagerReview(id, patch) {
  return fetchJSON(`${BASE}/api/reviews/manager-reviews/${id}/`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(patch),
  });
}

export async function deleteManagerReview(id) {
  return fetchJSON(`${BASE}/api/reviews/manager-reviews/${id}/`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}

/* -------------------------
   Peer Feedback
   ------------------------- */
export async function listPeerFeedback(params = {}) {
  return fetchJSON(`${BASE}/api/reviews/peer-feedback/${qs(params)}`, {
    headers: authHeaders(),
  });
}

export async function getPeerFeedback(id) {
  return fetchJSON(`${BASE}/api/reviews/peer-feedback/${id}/`, {
    headers: authHeaders(),
  });
}

export async function createPeerFeedback(payload) {
  return fetchJSON(`${BASE}/api/reviews/peer-feedback/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function patchPeerFeedback(id, patch) {
  return fetchJSON(`${BASE}/api/reviews/peer-feedback/${id}/`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(patch),
  });
}

export async function deletePeerFeedback(id) {
  return fetchJSON(`${BASE}/api/reviews/peer-feedback/${id}/`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}

export async function myPeerFeedback(params = {}) {
  return fetchJSON(`${BASE}/api/reviews/peer-feedback/my_feedback/${qs(params)}`, {
    headers: authHeaders(),
  });
}

/* -------------------------
   Default export
   ------------------------- */
export default {
  // cycles
  listReviewCycles,
  getReviewCycle,
  createReviewCycle,
  updateReviewCycle,
  patchReviewCycle,
  deleteReviewCycle,
  activateReviewCycle,
  completeReviewCycle,
  getCycleStatistics,

  // reviews
  listReviews,
  getReview,
  createReview,
  patchReview,
  deleteReview,
  calculateRating,
  myReviews,
  pendingReviews,

  // self-assessments
  listSelfAssessments,
  getSelfAssessment,
  createSelfAssessment,
  patchSelfAssessment,
  deleteSelfAssessment,

  // manager reviews
  listManagerReviews,
  getManagerReview,
  createManagerReview,
  patchManagerReview,
  deleteManagerReview,

  // peer feedback
  listPeerFeedback,
  getPeerFeedback,
  createPeerFeedback,
  patchPeerFeedback,
  deletePeerFeedback,
  myPeerFeedback,
};
