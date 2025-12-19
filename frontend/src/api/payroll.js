// src/api/payroll.js
// Full-featured helper for Day 16 Payroll APIs.
// Backwards-compatible; adds robust fallbacks for employee lookups.

const BASE = (process.env.REACT_APP_API_BASE || "http://localhost:8000").replace(/\/$/, "");

function getAuthToken() {
  return (
    localStorage.getItem("access_token") ||
    localStorage.getItem("access") ||
    localStorage.getItem("token") ||
    localStorage.getItem("auth_token") ||
    null
  );
}

function buildHeaders(extra = {}) {
  const token = getAuthToken();
  const headers = { Accept: "application/json", ...extra };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function fetchRaw(url, options = {}) {
  const merged = {
    method: options.method || "GET",
    headers: buildHeaders(options.headers || {}),
    body: options.body ?? undefined,
  };
  return fetch(url, merged);
}

async function fetchJSON(url, options = {}) {
  const res = await fetchRaw(url, options);
  const raw = await res.text().catch(() => "");
  let parsed = null;
  try {
    parsed = raw ? JSON.parse(raw) : null;
  } catch {
    parsed = raw || null;
  }

  if (!res.ok) {
    const err = new Error(`HTTP error! Status: ${res.status}, Message: ${raw || res.statusText}`);
    err.status = res.status;
    err.body = parsed;
    throw err;
  }
  if (!raw) return null;
  return parsed;
}

function qs(params = {}) {
  const s = new URLSearchParams(params).toString();
  return s ? "?" + s : "";
}

/* ----------------------
   Utilities exported
   ---------------------- */
export function checkResponse(response) {
  if (!response) throw new Error("No response");
  if (response.ok) return response.json();
  return response.json().then((j) => {
    const err = new Error(j?.detail || "Request failed");
    err.status = response.status;
    err.body = j;
    throw err;
  }).catch(() => {
    const err = new Error(response.statusText || "Request failed");
    err.status = response.status;
    throw err;
  });
}

export function statusChip(status) {
  const map = {
    GENERATED: { label: 'Generated', color: 'default' },
    APPROVED: { label: 'Approved', color: 'info' },
    PAID: { label: 'Paid', color: 'success' },
    ON_HOLD: { label: 'On Hold', color: 'warning' }
  };
  return map[status] ?? { label: status || 'Unknown', color: 'default' };
}

export function currencyINR(amount) {
  const num = typeof amount === "number" ? amount : parseFloat(amount) || 0;
  return `₹${num.toLocaleString("en-IN", { minimumFractionDigits: 2 })}`;
}

/* ----------------------
   Helper logic for safer GET lists with employee param fallbacks
   (QUIET: no fetch/response logs; only errors are logged)
   ---------------------- */

/**
 * Try fetching list at `path` with provided params. If server returns 500/404
 * and params.employee exists, try alternate query param keys and candidate forms.
 *
 * path: e.g. '/api/payroll/payslips/'
 * params: object - may include employee key (string|number)
 */
async function safeGetList(path, params = {}) {
  const tryFetch = async (p) => {
    const url = `${BASE.replace(/\/$/, "")}${path}${qs(p)}`;
    return fetchJSON(url, { method: "GET" });
  };

  // try primary call
  try {
    const res = await tryFetch(params);
    return res;
  } catch (err) {
    // only log on error
    console.error(`[API] Error fetching ${path}:`, err);

    // if it's not 500/404, rethrow (auth errors bubble)
    if (!err || (err.status && err.status !== 500 && err.status !== 404)) throw err;
    // proceed to fallbacks if we had an employee param to adjust
  }

  // If no employee param then nothing else to try
  if (params.employee == null) {
    // final attempt: call without params
    try {
      return await tryFetch({});
    } catch (e) {
      throw e;
    }
  }

  // Normalize candidate value
  const rawVal = params.employee;
  const valStr = rawVal == null ? "" : String(rawVal);
  const candidates = [];

  // If looks like resource URL ending in id e.g. /api/hr/employees/6/
  const m = valStr.match(/\/(\d+)\/?$/);
  if (m) {
    candidates.push(Number(m[1]));
  }

  // If purely numeric
  if (/^\d+$/.test(valStr)) {
    candidates.push(Number(valStr));
    candidates.push(valStr);
  }

  // If looks like email
  if (valStr.includes("@")) {
    candidates.push(valStr); // email form

    // email resource forms some backends accept
    candidates.push(`/api/auth/users/${encodeURIComponent(valStr)}/`);
    candidates.push(`/api/users/${encodeURIComponent(valStr)}/`);
  }

  // keep original value last
  candidates.push(valStr);

  // alternative query keys to try
  const altKeys = ["employee", "employee_id", "user", "user__email", "employee_profile", "employee_email"];

  // Try many combinations
  for (const cand of candidates) {
    for (const key of altKeys) {
      const p = { ...params };
      // set the single key and delete employee to avoid duplicates
      delete p.employee;
      p[key] = cand;
      try {
        const res = await tryFetch(p);
        return res;
      } catch (err) {
        // if auth error, bubble up
        if (err && (err.status === 401 || err.status === 403)) throw err;
        // else continue trying
      }
    }
  }

  // Final fallback: if candidate is email, attempt to resolve user id via users endpoint
  if (valStr.includes("@")) {
    const userEndpoints = ["/api/auth/users/", "/api/users/"];
    for (const ue of userEndpoints) {
      try {
        const listRes = await fetchJSON(`${BASE}${ue}${qs({ email: valStr })}`);
        // listRes may be array or {results:[]}
        let users = [];
        if (Array.isArray(listRes)) users = listRes;
        else if (listRes && Array.isArray(listRes.results)) users = listRes.results;
        if (users.length > 0) {
          const uid = users[0].id ?? users[0].pk;
          if (uid != null) {
            try {
              const res = await tryFetch({ ...params, employee: uid });
              return res;
            } catch (err) {
              if (err && (err.status === 401 || err.status === 403)) throw err;
            }
          }
        }
      } catch (e) {
        // ignore and continue
        if (e && (e.status === 401 || e.status === 403)) throw e;
      }
    }
  }

  // nothing worked; raise a helpful error (attempt original fetch once more to get real backend message)
  try {
    return await tryFetch(params);
  } catch (finalErr) {
    throw finalErr;
  }
}

/* ----------------------
   Salary Structures
   ---------------------- */
export async function getSalaryStructures(params = {}) {
  const urlPath = `/api/payroll/salary-structures/`;
  try {
    const data = await safeGetList(urlPath, params);
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.results)) return data.results;
    return [];
  } catch (err) {
    if (err?.status === 404) return [];
    throw err;
  }
}

export async function getSalaryStructureById(id) {
  return fetchJSON(`${BASE}/api/payroll/salary-structures/${id}/`);
}

export async function createSalaryStructure(payload) {
  return fetchJSON(`${BASE}/api/payroll/salary-structures/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function patchSalaryStructure(id, payload) {
  return fetchJSON(`${BASE}/api/payroll/salary-structures/${id}/`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deleteSalaryStructure(id) {
  return fetchJSON(`${BASE}/api/payroll/salary-structures/${id}/`, { method: "DELETE" });
}

/* ----------------------
   Employee salaries / assignments
   ---------------------- */
export async function getAllPayrolls(params = {}) {
  const url = `${BASE}/api/payroll/employee-salaries/${qs(params)}`;
  try {
    const data = await fetchJSON(url);
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.results)) return data.results;
    return [];
  } catch (err) {
    if (err?.status === 404) return [];
    throw err;
  }
}

export async function getPayrollById(id) {
  return fetchJSON(`${BASE}/api/payroll/employee-salaries/${id}/`);
}

export async function patchPayroll(id, payload) {
  return fetchJSON(`${BASE}/api/payroll/employee-salaries/${id}/`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// Convenience alias used by the UI to update employee salary overrides.
// Backend endpoint: PATCH /api/payroll/employee-salaries/{id}/
export async function updateEmployeeSalaryOverride(id, payload) {
  // reuse existing patchPayroll implementation
  return patchPayroll(id, payload);
}

export async function deletePayroll(id) {
  return fetchJSON(`${BASE}/api/payroll/employee-salaries/${id}/`, { method: "DELETE" });
}

export async function getPayrollsByEmployee(employeeId) {
  if (!employeeId) return [];
  const url = `${BASE}/api/payroll/employee-salaries/${qs({ employee: employeeId })}`;
  try {
    const data = await fetchJSON(url);
    const arr = Array.isArray(data) ? data : data?.results ?? [];
    return Array.isArray(arr) ? arr : [];
  } catch (err) {
    if (err && (err.status === 401 || err.status === 403)) throw err;
    return [];
  }
}

/**
 * getMyPayroll()
 * - try /my_salary/ first (preferred)
 * - if 404 or null, try to resolve current user id/email from common endpoints, then call getPayrollsByEmployee
 */
export async function getMyPayroll() {
  const url = `${BASE}/api/payroll/employee-salaries/my_salary/`;
  try {
    const data = await fetchJSON(url);
    // prefer single object or first of list
    if (Array.isArray(data)) return data.length ? data[0] : null;
    if (data && Array.isArray(data.results)) return data.results.length ? data.results[0] : null;
    return data;
  } catch (err) {
    // auth errors bubble upwards
    if (err && (err.status === 401 || err.status === 403)) throw err;
    // if 404 or other, try to resolve user then fallback
  }

  // try to discover user id/email via common endpoints
  const userEndpoints = ["/api/auth/me/", "/api/auth/user/", "/api/auth/users/me/", "/api/users/me/", "/api/auth/users/"];
  for (const ue of userEndpoints) {
    try {
      // for list endpoint (/api/auth/users/?email=...), skip here (we'll use other logic)
      if (ue.endsWith("/users/") && getAuthToken()) {
        // don't blindly call list without query - skip
      } else {
        const res = await fetchJSON(`${BASE}${ue}`);
        // attempt to extract id or email
        if (res) {
          const uid = res.id ?? res.pk;
          const email = res.email;
          if (uid != null) {
            const arr = await getPayrollsByEmployee(uid);
            if (Array.isArray(arr) && arr.length > 0) return arr[0];
          }
          if (email) {
            // try find user by email then id
            try {
              const ulist = await fetchJSON(`${BASE}/api/auth/users/${qs({ email })}`);
              // some backends might not support that; ignore errors
            } catch (e) {
              // ignore
            }
            const arr = await getPayrollsByEmployee(email);
            if (Array.isArray(arr) && arr.length > 0) return arr[0];
          }
        }
      }
    } catch (e) {
      if (e && (e.status === 401 || e.status === 403)) throw e;
      // else try next
    }
  }

  return null;
}

/**
 * createPayroll(payload)
 * - resilient create (retries common resource-url forms for employee when backend expects a URL)
 */
export async function createPayroll(payload) {
  async function doPost(body) {
    return fetchJSON(`${BASE}/api/payroll/employee-salaries/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  }

  try {
    return await doPost(payload);
  } catch (err) {
    if (!err || err.status !== 400) throw err;

    const body = err.body ?? null;
    const employeeInvalid =
      (body && body.employee && (String(body.employee).toLowerCase().includes("invalid pk") || String(body.employee).toLowerCase().includes("does not exist"))) ||
      (typeof err.message === "string" && /invalid pk|does not exist/i.test(err.message));

    if (!employeeInvalid || payload.employee == null) throw err;

    let numericId = null;
    if (!isNaN(Number(payload.employee))) numericId = Number(payload.employee);

    const tried = [];
    const candidates = [];

    if (numericId != null) {
      candidates.push(`${BASE}/api/auth/users/${numericId}/`);
      candidates.push(`${BASE}/api/users/${numericId}/`);
      candidates.push(`${BASE}/api/accounts/users/${numericId}/`);
      candidates.push(`${BASE}/api/hr/employees/${numericId}/`);
      candidates.push(`${BASE}/api/dashboard/users/${numericId}/`);
    } else if (typeof payload.employee === "string") {
      candidates.push(`${BASE}/api/auth/users/${payload.employee}/`);
      candidates.push(`${BASE}/api/users/${payload.employee}/`);
    }

    let lastErr = err;
    for (const candidate of candidates) {
      if (tried.includes(candidate)) continue;
      tried.push(candidate);
      const newPayload = { ...payload, employee: candidate };
      try {
        const res = await doPost(newPayload);
        return res;
      } catch (retryErr) {
        lastErr = retryErr;
      }
    }

    if (typeof payload.employee === "string" && isNaN(Number(payload.employee))) {
      const nested = { ...payload, employee: { email: payload.employee } };
      try {
        const res = await doPost(nested);
        return res;
      } catch (nestedErr) {
        lastErr = nestedErr;
      }
    }

    throw lastErr;
  }
}

/* ----------------------
   Payslips helpers
   ---------------------- */
export async function getPayslips(params = {}) {
  const urlPath = `/api/payroll/payslips/`;
  try {
    const data = await safeGetList(urlPath, params);
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.results)) return data.results;
    return [];
  } catch (err) {
    if (err?.status === 404) return [];
    throw err;
  }
}

export async function getPayslipById(id) {
  return fetchJSON(`${BASE}/api/payroll/payslips/${id}/`);
}

export async function generatePayslips(payload) {
  return fetchJSON(`${BASE}/api/payroll/payslips/generate/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function approvePayslip(id) {
  return fetchJSON(`${BASE}/api/payroll/payslips/${id}/approve/`, { method: "POST" });
}

/**
 * markPayslipPaid(id, { paymentDate, paymentMode, reference })
 */
export async function markPayslipPaid(id, { paymentDate = null, paymentMode = null, reference = null } = {}) {
  const body = {};
  if (paymentDate) body.payment_date = paymentDate;
  if (paymentMode) body.payment_mode = paymentMode;
  if (reference) body.payment_reference = reference;
  return fetchJSON(`${BASE}/api/payroll/payslips/${id}/mark_paid/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export async function downloadPayslip(id) {
  const url = `${BASE}/api/payroll/payslips/${id}/download/`;
  const token = getAuthToken();
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(url, { method: "GET", headers });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    const err = new Error(`HTTP error! Status: ${res.status}, Message: ${txt || res.statusText}`);
    err.status = res.status;
    err.body = txt;
    throw err;
  }
  const blob = await res.blob();
  const cd = res.headers.get("content-disposition") || "";
  let filename = `payslip-${id}.pdf`;
  const m = /filename="?([^";]+)"?/.exec(cd);
  if (m && m[1]) filename = m[1];
  return { blob, filename };
}

export async function deletePayslip(id) {
  return fetchJSON(`${BASE}/api/payroll/payslips/${id}/`, { method: "DELETE" });
}

/* ----------------------
   Salary history
   ---------------------- */
export async function getSalaryHistory(params = {}) {
  const urlPath = `/api/payroll/salary-history/`;
  try {
    const data = await safeGetList(urlPath, params);
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.results)) return data.results;
    return [];
  } catch (err) {
    if (err?.status === 404) return [];
    throw err;
  }
}

export async function createSalaryHistory(payload) {
  return fetchJSON(`${BASE}/api/payroll/salary-history/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getSalaryHistoryById(id) {
  return fetchJSON(`${BASE}/api/payroll/salary-history/${id}/`);
}

export async function patchSalaryHistory(id, payload) {
  return fetchJSON(`${BASE}/api/payroll/salary-history/${id}/`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deleteSalaryHistory(id) {
  return fetchJSON(`${BASE}/api/payroll/salary-history/${id}/`, { method: "DELETE" });
}

/* ----------------------
   Deductions
   ---------------------- */
export async function getDeductions(params = {}) {
  const urlPath = `/api/payroll/deductions/`;
  try {
    const data = await safeGetList(urlPath, params);
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.results)) return data.results;
    return [];
  } catch (err) {
    if (err?.status === 404) return [];
    throw err;
  }
}

export async function createDeduction(payload) {
  return fetchJSON(`${BASE}/api/payroll/deductions/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getDeductionById(id) {
  return fetchJSON(`${BASE}/api/payroll/deductions/${id}/`);
}

export async function patchDeduction(id, payload) {
  return fetchJSON(`${BASE}/api/payroll/deductions/${id}/`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deleteDeduction(id) {
  return fetchJSON(`${BASE}/api/payroll/deductions/${id}/`, { method: "DELETE" });
}

/* ----------------------
   Backwards-compatible default exports
   ---------------------- */
export default {
  BASE,
  getAuthToken,
  buildHeaders,
  fetchRaw,
  fetchJSON,
  checkResponse,
  statusChip,
  currencyINR,
  // salary structures
  getSalaryStructures,
  getSalaryStructureById,
  createSalaryStructure,
  patchSalaryStructure,
  deleteSalaryStructure,
  // payrolls
  getAllPayrolls,
  getPayrollById,
  patchPayroll,
  updateEmployeeSalaryOverride, // convenience alias for patchPayroll
  deletePayroll,
  getPayrollsByEmployee,
  getMyPayroll,
  createPayroll,
  // payslips
  getPayslips,
  getPayslipById,
  generatePayslips,
  approvePayslip,
  markPayslipPaid,
  downloadPayslip,
  deletePayslip,
  // history
  getSalaryHistory,
  createSalaryHistory,
  getSalaryHistoryById,
  patchSalaryHistory,
  deleteSalaryHistory,
  // deductions
  getDeductions,
  createDeduction,
  getDeductionById,
  patchDeduction,
  deleteDeduction,
};
