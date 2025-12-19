// src/api/expenses.js  (FINAL FULLY FIXED VERSION)

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
  Object.keys(params).forEach((k) => {
    const v = params[k];
    if (v !== undefined && v !== null && v !== "") clean[k] = v;
  });
  const s = new URLSearchParams(clean).toString();
  return s ? `?${s}` : "";
}

async function fetchJSON(url, options = {}) {
  console.debug("API >", options.method || "GET", url);

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

/* ===========================
      CATEGORIES
=========================== */
export async function fetchExpenseCategories({ includeInactive = false } = {}) {
  const url = `${BASE}/api/expenses/categories/${includeInactive ? "?is_active=false" : ""}`;
  return fetchJSON(url, { headers: authHeaders() });
}

export async function createExpenseCategory(payload) {
  return fetchJSON(`${BASE}/api/expenses/categories/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function getExpenseCategory(id) {
  return fetchJSON(`${BASE}/api/expenses/categories/${id}/`, {
    headers: authHeaders(),
  });
}

export async function patchExpenseCategory(id, payload) {
  return fetchJSON(`${BASE}/api/expenses/categories/${id}/`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function deleteExpenseCategory(id) {
  return fetchJSON(`${BASE}/api/expenses/categories/${id}/`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}

/* ===========================
      CLAIMS
=========================== */
export async function fetchClaims(params = {}) {
  return fetchJSON(`${BASE}/api/expenses/claims/${qs(params)}`, {
    headers: authHeaders(),
  });
}

export async function fetchMyClaims(params = {}) {
  return fetchJSON(`${BASE}/api/expenses/claims/my_claims/${qs(params)}`, {
    headers: authHeaders(),
  });
}

export async function fetchClaimById(id) {
  return fetchJSON(`${BASE}/api/expenses/claims/${id}/`, {
    headers: authHeaders(),
  });
}

export async function createClaim(payload) {
  return fetchJSON(`${BASE}/api/expenses/claims/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function updateClaim(id, patch) {
  return fetchJSON(`${BASE}/api/expenses/claims/${id}/`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(patch),
  });
}

export async function submitClaim(id, notes = "") {
  return fetchJSON(`${BASE}/api/expenses/claims/${id}/submit/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ notes }),
  });
}

export async function reviewClaim(id, { action, reviewNotes = "", adjustedAmount = null } = {}) {
  const payload = { action, review_notes: reviewNotes };
  if (adjustedAmount != null) payload.adjusted_amount = adjustedAmount;

  return fetchJSON(`${BASE}/api/expenses/claims/${id}/approve/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function reimburseClaim(id, payload = {}) {
  return fetchJSON(`${BASE}/api/expenses/claims/${id}/mark_reimbursed/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
}

export async function fetchPendingApprovals(params = {}) {
  return fetchJSON(`${BASE}/api/expenses/claims/pending_approvals/${qs(params)}`, {
    headers: authHeaders(),
  });
}

export async function fetchExpenseStatistics(params = {}) {
  return fetchJSON(`${BASE}/api/expenses/claims/statistics/${qs(params)}`, {
    headers: authHeaders(),
  });
}

/* ===========================
      RECEIPTS
=========================== */
export async function fetchReceipts(params = {}) {
  return fetchJSON(`${BASE}/api/expenses/receipts/${qs(params)}`, {
    headers: authHeaders(),
  });
}

export async function uploadReceipt({
  claimId = null,
  file,
  amount = null,
  receiptDate = null,
  vendorName = null,
  receiptNumber = null,
} = {}) {
  const fd = new FormData();
  if (claimId) fd.append("claim", claimId);
  fd.append("file", file);
  if (amount != null) fd.append("amount", amount);
  if (receiptDate) fd.append("receipt_date", receiptDate);
  if (vendorName) fd.append("vendor_name", vendorName);
  if (receiptNumber) fd.append("receipt_number", receiptNumber);

  return fetchJSON(`${BASE}/api/expenses/receipts/`, {
    method: "POST",
    headers: authHeaders(),
    body: fd,
  });
}

export async function verifyReceipt(id, notes = "") {
  return fetchJSON(`${BASE}/api/expenses/receipts/${id}/verify/`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ verification_notes: notes }),
  });
}

export async function deleteReceipt(id) {
  return fetchJSON(`${BASE}/api/expenses/receipts/${id}/`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}

/* ===========================
      HISTORY
=========================== */
export async function fetchClaimHistory(params = {}) {
  return fetchJSON(`${BASE}/api/expenses/history/${qs(params)}`, {
    headers: authHeaders(),
  });
}

export default {
  fetchExpenseCategories,
  createExpenseCategory,
  getExpenseCategory,
  patchExpenseCategory,
  deleteExpenseCategory,
  fetchClaims,
  fetchMyClaims,
  fetchClaimById,
  createClaim,
  updateClaim,
  submitClaim,
  reviewClaim,
  reimburseClaim,
  fetchPendingApprovals,
  fetchExpenseStatistics,
  fetchReceipts,
  uploadReceipt,
  verifyReceipt,
  deleteReceipt,
  fetchClaimHistory,
};
