// src/pages/AttendancePage.jsx
// Enhanced UI with Bootstrap modals for forms (no extra libraries)

import React, { useEffect, useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";

/*
  Usage:
  - Ensure backend at http://localhost:8000
  - Login elsewhere and set localStorage.setItem('access_token', token)
  - Navigate to this page in your app
*/

const API_ROOT = "http://localhost:8000/api/attendance";

function authHeaders() {
  const token = localStorage.getItem("access_token");
  return {
    Authorization: token ? `Bearer ${token}` : "",
    "Content-Type": "application/json",
  };
}

/* --- API helpers --- */
async function apiGet(path) {
  const res = await fetch(`${API_ROOT}${path}`, { method: "GET", headers: authHeaders() });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(`${res.status} ${txt}`);
  }
  return res.json();
}
async function apiPost(path, body = {}) {
  const res = await fetch(`${API_ROOT}${path}`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: "unknown error" }));
    throw new Error(JSON.stringify(err));
  }
  return res.json();
}

/* --- optional reverse geocode using Nominatim (free) --- */
async function reverseGeocode(lat, lon) {
  try {
    const u = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}`;
    const r = await fetch(u);
    if (!r.ok) return "";
    const j = await r.json();
    return j.display_name || "";
  } catch (e) {
    return "";
  }
}

/* --- Small UX Helpers --- */
function timeOnly(dtStr) {
  if (!dtStr) return "-";
  try {
    const s = String(dtStr).trim();
    const plainTimeMatch = s.match(/^(\d{1,2}):(\d{2})(?::\d{2})?$/);
    if (plainTimeMatch) {
      const hh = plainTimeMatch[1].padStart(2, "0");
      const mm = plainTimeMatch[2];
      return `${hh}:${mm}`;
    }
    const d = new Date(s);
    if (!isNaN(d.getTime())) {
      const parts = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
      const m = parts.match(/(\d{1,2}):(\d{2})/);
      if (m) {
        const hh = m[1].padStart(2, "0");
        const mm = m[2];
        return `${hh}:${mm}`;
      }
      return parts;
    }
    const fallback = s.match(/(\d{1,2}:\d{2})/);
    if (fallback) return fallback[1];
    return s;
  } catch (e) {
    try {
      const d = new Date(dtStr);
      if (!isNaN(d.getTime())) {
        return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
      }
    } catch {}
    return String(dtStr);
  }
}

function dateOnly(dtStr) {
  if (!dtStr) return "-";
  try {
    const s = String(dtStr).trim();
    if (s.includes("T")) {
      const left = s.split("T")[0];
      if (left && /^\d{4}-\d{2}-\d{2}$/.test(left)) {
        const [y, m, d] = left.split("-");
        const dd = new Date(Number(y), Number(m) - 1, Number(d));
        if (!isNaN(dd)) return dd.toLocaleDateString();
        return left;
      }
    }
    const plain = s.match(/(\d{4}-\d{2}-\d{2})/);
    if (plain) {
      const [y, m, d] = plain[1].split("-");
      const dd = new Date(Number(y), Number(m) - 1, Number(d));
      if (!isNaN(dd)) return dd.toLocaleDateString();
      return plain[1];
    }
    const d = new Date(s);
    if (!isNaN(d.getTime())) return d.toLocaleDateString();
    return s;
  } catch (e) {
    try {
      const d = new Date(dtStr);
      if (!isNaN(d.getTime())) return d.toLocaleDateString();
    } catch {}
    return String(dtStr);
  }
}

/* ---------------- Role detection helper ---------------- */
function getUserRole() {
  try {
    const direct = localStorage.getItem("user_role") || localStorage.getItem("role");
    if (direct) return String(direct).toLowerCase();

    const userJson = localStorage.getItem("user");
    if (userJson) {
      try {
        const u = JSON.parse(userJson);
        const role = u && (u.role || u.user_role || u.user_type || u.type);
        if (role) return String(role).toLowerCase();
      } catch {}
    }

    const token = localStorage.getItem("access_token");
    if (token) {
      const parts = token.split(".");
      if (parts.length >= 2) {
        const payload = parts[1];
        const pad = payload.length % 4 === 2 ? "==" : payload.length % 4 === 3 ? "=" : payload.length % 4 === 0 ? "" : "";
        const safe = payload.replace(/-/g, "+").replace(/_/g, "/") + pad;
        try {
          const json = JSON.parse(atob(safe));
          const role = json.role || json.user_role || json.role_name || json.user_type || json.type || (json.roles && (Array.isArray(json.roles) ? json.roles[0] : json.roles));
          if (role) return String(role).toLowerCase();
        } catch {}
      }
    }
  } catch (e) {}
  return null;
}

/* utility: badge for status */
function StatusBadge({ status }) {
  const s = String(status || "").toLowerCase();
  if (s.includes("approve") || s === "approved" || s === "accepted") return <span className="badge bg-success">Approved</span>;
  if (s.includes("reject") || s === "rejected") return <span className="badge bg-danger">Rejected</span>;
  if (s.includes("pending") || s === "pending" || s === "") return <span className="badge bg-warning text-dark">Pending</span>;
  // fallback
  return <span className="badge bg-secondary">{status}</span>;
}

/* ---------------- Components ---------------- */

// Generic simple modal wrapper using Bootstrap markup but controlled by React (no bootstrap JS required)
function Modal({ title, show, onClose, children, size = "" }) {
  if (!show) return null;
  return (
    <div>
      <div className="modal show d-block" tabIndex="-1" role="dialog" aria-modal="true">
        <div className={`modal-dialog ${size}`} role="document">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">{title}</h5>
              <button type="button" className="btn-close" aria-label="Close" onClick={onClose}></button>
            </div>
            <div className="modal-body">{children}</div>
          </div>
        </div>
      </div>
      <div className="modal-backdrop show" onClick={onClose}></div>
    </div>
  );
}

/* ---------- My Requests component (shows WFH + Regularization statuses) ---------- */
function MyRequests({ show, onClose, refreshSignal }) {
  const [wfh, setWfh] = useState([]);
  const [regulars, setRegulars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => { if (show) load(); }, [show, refreshSignal]);

  async function tryFetch(prefPaths) {
    for (const p of prefPaths) {
      try {
        const data = await apiGet(p);
        // prefer list directly, or results property
        if (Array.isArray(data)) return data;
        if (Array.isArray(data.results)) return data.results;
        // maybe single object -> wrap
        if (Array.isArray(data.items)) return data.items;
      } catch (e) {
        // try next
      }
    }
    // nothing found
    return [];
  }

  async function load() {
    setLoading(true);
    setErr(null);
    try {
      const [w, r] = await Promise.all([
        tryFetch(["/wfh-requests/my-requests/", "/wfh-requests/"]),
        tryFetch(["/regularizations/my-requests/", "/regularizations/"]),
      ]);
      setWfh(w);
      setRegulars(r);
    } catch (e) {
      console.error("myrequests load:", e);
      setErr("Failed to load requests.");
      setWfh([]);
      setRegulars([]);
    } finally { setLoading(false); }
  }

  return (
    <Modal title="My Requests" show={show} onClose={onClose} size="modal-lg">
      <div>
        {loading ? <div className="text-center py-3">Loading...</div> : err ? <div className="alert alert-danger">{err}</div> : (
          <div className="row">
            <div className="col-12 mb-3 d-flex justify-content-between align-items-center">
              <h6 className="mb-0">WFH Requests <small className="text-muted">({wfh.length})</small></h6>
              <button className="btn btn-sm btn-outline-secondary" onClick={load}>Refresh</button>
            </div>

            <div className="col-12 mb-4">
              {wfh.length === 0 ? <div className="text-muted">No WFH requests</div> : (
                <div className="list-group">
                  {wfh.map((item) => (
                    <div key={item.id || item.pk || `${item.date}-${item.status}`} className="list-group-item d-flex justify-content-between align-items-start">
                      <div>
                        <div><strong>{item.user_name || item.requested_by_name || "You"}</strong> • <small className="muted-small">{dateOnly(item.date || item.requested_date || item.created_at)}</small></div>
                        <div className="muted-small">{item.reason || item.note || ""}</div>
                        {item.manager_comment && <div className="muted-small mt-1"><strong>Manager:</strong> {item.manager_comment}</div>}
                      </div>
                      <div className="text-end">
                        <StatusBadge status={item.status} />
                        <div className="muted-small mt-1">{item.updated_at ? timeOnly(item.updated_at) : (item.created_at ? timeOnly(item.created_at) : "")}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="col-12 mb-3">
              <h6 className="mb-0">Regularization Requests <small className="text-muted">({regulars.length})</small></h6>
            </div>

            <div className="col-12">
              {regulars.length === 0 ? <div className="text-muted">No regularization requests</div> : (
                <div className="list-group">
                  {regulars.map((item) => (
                    <div key={item.id || item.pk || `${item.attendance}-${item.status}`} className="list-group-item d-flex justify-content-between align-items-start">
                      <div>
                        <div><strong>{item.requested_by_name || item.user_name || "You"}</strong> • <small className="muted-small">{dateOnly(item.attendance_date || item.date || item.created_at)}</small></div>
                        <div className="muted-small">Requested: {item.requested_check_in || item.requested_time || "-"}</div>
                        <div className="muted-small">{item.reason || ""}</div>
                        {item.manager_comment && <div className="muted-small mt-1"><strong>Manager:</strong> {item.manager_comment}</div>}
                      </div>
                      <div className="text-end">
                        <StatusBadge status={item.status} />
                        <div className="muted-small mt-1">{item.updated_at ? timeOnly(item.updated_at) : (item.created_at ? timeOnly(item.created_at) : "")}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      <div className="mt-3 text-end"><button className="btn btn-sm btn-outline-secondary" onClick={onClose}>Close</button></div>
    </Modal>
  );
}

/* ---------------- Existing components (AttendanceDashboard, forms, history, manager) ---------------- */

function AttendanceDashboard({ onOpenCheckin, onOpenCheckout, onOpenHistory, onOpenRegularize, onOpenWFH, onOpenMyRequests, refreshAll }) {
  const [today, setToday] = useState(null);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [overtimeRecords, setOvertimeRecords] = useState([]);
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [alert, setAlert] = useState(null);

  useEffect(() => { load(); }, [month, year]);

  async function load() {
    setLoading(true);
    setAlert(null);
    try {
      const [t, s, o] = await Promise.all([
        apiGet("/attendance/today-status/").catch(()=>null),
        apiGet(`/attendance/monthly-summary/?month=${month}&year=${year}`).catch(()=>null),
        apiGet("/attendance/overtime-records/?month=" + month + "&year=" + year).catch(()=>[]),
      ]);
      setToday(t);
      setSummary(s);
      setOvertimeRecords(Array.isArray(o) ? o : (o.results || []));
    } catch (e) {
      console.error("Dashboard load error", e);
      setAlert({ type: "danger", message: "Failed to load dashboard data." });
      setToday(null);
      setSummary(null);
      setOvertimeRecords([]);
    } finally { setLoading(false); }
  }

  return (
    <div className="container py-3">
      <style>{`.card-compact{border-radius:10px}.muted-small{color:#6c757d}.stat-box{padding:10px;border-radius:8px;background:#fff;box-shadow:0 2px 6px rgba(0,0,0,0.03)}`}</style>
      {alert && <div className={`alert alert-${alert.type} py-2`} role="alert">{alert.message}</div>}

      <br />

      <div className="row g-3">
        <div className="col-12 col-lg-6">
          <div className="card shadow-sm card-compact h-100">
            <div className="card-body d-flex flex-column">
              <h5 className="card-title">Today's Status</h5>
              {loading ? <div className="text-center py-3">Loading...</div> : (!today || today.checked_in === false ? (
                <div className="my-auto text-center">
                  <p className="muted-small">You haven't checked in today.</p>
                  <div className="row g-2 justify-content-center mt-2">
                    <div className="col-8 col-sm-6"><button className="btn btn-success btn-lg w-100" onClick={onOpenCheckin}>Check In</button></div>
                    <div className="col-8 col-sm-6"><button className="btn btn-outline-secondary btn-lg w-100" onClick={onOpenRegularize}>Regularize</button></div>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="d-flex justify-content-between align-items-start">
                    <div>
                      <h6 className="mb-0">{today.user_name || "You"}</h6>
                      <small className="muted-small">{today.shift_name || ""}</small>
                    </div>
                    <div className="text-end">
                      <span className={`badge ${today.status === 'present' ? 'bg-success' : 'bg-secondary'}`}>{today.status}</span>
                      <div className="muted-small">{dateOnly(today.date)}</div>
                    </div>
                  </div>

                  <hr />

                  <div className="d-flex flex-column gap-2">
                    <div className="d-flex justify-content-between">
                      <div>
                        <div className="muted-small">Check-in</div>
                        <div className="fw-bold">{timeOnly(today.check_in_time)}</div>
                        <div className="muted-small">{today.check_in_address || today.check_in_location}</div>
                      </div>
                      <div className="text-end">
                        <div className="muted-small">Check-out</div>
                        <div className="fw-bold">{today.check_out_time ? timeOnly(today.check_out_time) : <button className="btn btn-outline-primary btn-sm ms-2" onClick={onOpenCheckout}>Check Out</button>}</div>
                      </div>
                    </div>

                    <div className="d-flex gap-3 flex-wrap mt-2">
                      <div className="stat-box text-center"><div className="muted-small">Work hours</div><div className="fw-bold">{today.work_hours ?? "0.00"} hrs</div></div>
                      <div className="stat-box text-center"><div className="muted-small">Overtime</div><div className="fw-bold text-warning">{today.overtime_hours ?? "0.00"} hrs</div></div>
                      {today.is_late && <div className="stat-box text-center text-danger"><div className="muted-small">Late by</div><div className="fw-bold">{today.late_by_minutes} min</div></div>}
                    </div>

                    <div className="d-flex gap-2 mt-3">
                      <button className="btn btn-outline-secondary btn-sm px-3" onClick={onOpenRegularize}>Regularize</button>
                      <button className="btn btn-outline-secondary btn-sm px-3" onClick={onOpenWFH}>Request WFH</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col-12 col-lg-6">
          <div className="card shadow-sm mb-3 card-compact">
            <div className="card-body">
              <h5 className="card-title d-flex align-items-center">
                <span className="me-auto">Monthly Summary</span>
                <div className="d-flex gap-2 align-items-center">
                  <select className="form-select form-select-sm" value={month} onChange={e => setMonth(Number(e.target.value))} style={{width: '90px'}}>
                    {Array.from({length:12}).map((_,i)=><option key={i+1} value={i+1}>{i+1}</option>)}
                  </select>
                  <input className="form-control form-control-sm" style={{width:'90px'}} value={year} onChange={e=>setYear(e.target.value)} />
                </div>
              </h5>
              {summary ? (
                <div className="row text-center mt-3">
                  <div className="col-4 mb-2"><div className="h4 mb-0">{summary.present_days}</div><small className="muted-small">Present</small></div>
                  <div className="col-4 mb-2"><div className="h4 mb-0">{summary.absent_days}</div><small className="muted-small">Absent</small></div>
                  <div className="col-4 mb-2"><div className="h4 mb-0">{summary.late_count}</div><small className="muted-small">Late</small></div>

                  <div className="col-4 mt-3"><div className="h5 mb-0">{summary.total_overtime} hrs</div><small className="muted-small">Overtime</small></div>
                  <div className="col-4 mt-3"><div className="h5 mb-0">{summary.total_work_hours} hrs</div><small className="muted-small">Work Hours</small></div>
                  <div className="col-4 mt-3"><div className="h5 mb-0">{summary.attendance_percentage}%</div><small className="muted-small">Attendance</small>
                    <div className="progress mt-2" style={{height:8}}><div className="progress-bar" role="progressbar" style={{width: `${summary.attendance_percentage}%`}} aria-valuenow={summary.attendance_percentage} aria-valuemin="0" aria-valuemax="100"></div></div>
                  </div>
                </div>
              ) : <div className="text-muted mt-3">No summary available</div>}
            </div>
          </div>

          <div className="card shadow-sm card-compact">
            <div className="card-body">
              <h5 className="card-title d-flex align-items-center"><span className="me-auto">Overtime Records</span><small className="muted-small ms-2">({overtimeRecords.length})</small></h5>

              {overtimeRecords.length === 0 ? <div className="text-muted">No overtime records for selected month</div> : (
                <div style={{maxHeight: "220px", overflowY: "auto"}}>
                  {overtimeRecords.slice(0,8).map((o, idx) => (
                    <div key={o.id || idx} className="d-flex justify-content-between align-items-center py-2 border-bottom">
                      <div><div><strong>{o.user_name || o.user_email || `User ${o.user}`}</strong></div><div className="muted-small">{dateOnly(o.date || o.created_at)} • {o.reason || ""}</div></div>
                      <div className="text-end"><div className="fw-bold text-warning">{o.overtime_hours ?? o.hours ?? "0.00"} hrs</div><div className="muted-small">{o.status || ""}</div></div>
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-2 d-flex justify-content-end">
                <div className="d-flex gap-2">
                  {/* <button className="btn btn-sm btn-outline-primary px-2" onClick={() => window.alert('Open full overtime page (not implemented)')}>View All</button>
                   */}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-3 d-flex flex-wrap gap-2">
        <button className="btn btn-primary btn-sm px-3" onClick={onOpenCheckin}>Check In</button>
        <button className="btn btn-danger btn-sm px-3" onClick={onOpenCheckout}>Check Out</button>
        <button className="btn btn-outline-secondary btn-sm px-3" onClick={onOpenRegularize}>Regularize</button>
        <button className="btn btn-outline-secondary btn-sm px-3" onClick={onOpenWFH}>Request WFH</button>
        <button className="btn btn-info btn-sm px-3" onClick={onOpenHistory}>History</button>
        <button className="btn btn-outline-info btn-sm px-3" onClick={onOpenMyRequests}>My Requests</button>
      </div>
    </div>
  );
}

/* ---------- Forms (same logic as before) ---------- */
function CheckInForm({ onDone, close }) {
  const [location, setLocation] = useState("");
  const [address, setAddress] = useState("");
  const [shiftId, setShiftId] = useState(1);
  const [loading, setLoading] = useState(false);
  const [locLoading, setLocLoading] = useState(false);
  const [shifts, setShifts] = useState([]);

  useEffect(() => { loadShifts(); }, []);
  async function loadShifts() {
    try {
      const data = await apiGet("/shifts/");
      setShifts(Array.isArray(data) ? data : []);
      if (data && data.length) setShiftId(data[0].id || data[0].pk || 1);
    } catch (e) { console.warn("loadShifts:", e); }
  }

  async function useCurrentLocation() {
    if (!navigator.geolocation) return alert("Geolocation not supported");
    setLocLoading(true);
    navigator.geolocation.getCurrentPosition(async (pos) => {
      const lat = pos.coords.latitude.toFixed(6);
      const lon = pos.coords.longitude.toFixed(6);
      const loc = `${lat}, ${lon}`;
      setLocation(loc);
      const addr = await reverseGeocode(lat, lon);
      if (addr) setAddress(addr);
      setLocLoading(false);
    }, (err) => { alert("Location error: " + err.message); setLocLoading(false); }, { timeout: 10000 });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!location) return alert("Please provide location or tap Use Current Location");
    setLoading(true);
    try {
      const payload = { location, address, shift_id: shiftId };
      const res = await apiPost("/attendance/checkin/", payload);
      alert(res.message || "Checked in");
      onDone && onDone(res.attendance || res);
      close();
    } catch (err) {
      console.error("checkin:", err);
      alert("Check-in failed: " + (err.message || err));
    } finally { setLoading(false); }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="mb-2">
        <label className="form-label">Location (lat, lon)</label>
        <div className="input-group">
          <input value={location} onChange={e=>setLocation(e.target.value)} className="form-control" placeholder="Latitude, Longitude" />
          <button type="button" className="btn btn-outline-secondary btn-sm" onClick={useCurrentLocation} disabled={locLoading}>{locLoading ? "Locating..." : "Use Current"}</button>
        </div>
      </div>

      <div className="mb-2">
        <label className="form-label">Address</label>
        <input value={address} onChange={e=>setAddress(e.target.value)} className="form-control" placeholder="Office address or current location" />
      </div>

      <div className="mb-3">
        <label className="form-label">Shift</label>
        <select className="form-select" value={shiftId} onChange={e=>setShiftId(e.target.value)}>
          {shifts.length === 0 ? (
            <>
              <option value="1">Morning Shift (9:00 - 18:00)</option>
              <option value="2">Evening Shift</option>
              <option value="3">Night Shift</option>
            </>
          ) : shifts.map(s => <option key={s.id || s.pk} value={s.id || s.pk}>{s.name || s.shift_name || `Shift ${s.id}`}</option>)}
        </select>
      </div>

      <div className="d-flex gap-2">
        <button className="btn btn-primary" disabled={loading}>{loading ? "Checking..." : "Check In"}</button>
        <button type="button" className="btn btn-outline-secondary" onClick={() => { setLocation(""); setAddress(""); }}>Reset</button>
      </div>
    </form>
  );
}

function CheckOutForm({ onDone, close }) {
  const [remarks, setRemarks] = useState("");
  const [location, setLocation] = useState("");
  const [address, setAddress] = useState("");
  const [loading, setLoading] = useState(false);
  const [locLoading, setLocLoading] = useState(false);

  async function useCurrentLocation() {
    if (!navigator.geolocation) return alert("Geolocation not supported");
    setLocLoading(true);
    navigator.geolocation.getCurrentPosition(async (pos) => {
      const lat = pos.coords.latitude.toFixed(6);
      const lon = pos.coords.longitude.toFixed(6);
      const loc = `${lat}, ${lon}`;
      setLocation(loc);
      const addr = await reverseGeocode(lat, lon);
      if (addr) setAddress(addr);
      setLocLoading(false);
    }, (err) => { alert("Location error: " + err.message); setLocLoading(false); }, { timeout: 10000 });
  }

  async function submitCheckout(e) {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = { location, address, remarks };
      const res = await apiPost("/attendance/checkout/", payload);
      alert(res.message || "Checked out");
      onDone && onDone(res.attendance || res);
      close();
    } catch (err) {
      console.error("checkout:", err);
      alert("Check-out failed: " + (err.message || err));
    } finally { setLoading(false); }
  }

  return (
    <form onSubmit={submitCheckout}>
      <div className="mb-2">
        <label className="form-label">Location (optional)</label>
        <div className="input-group">
          <input value={location} onChange={e => setLocation(e.target.value)} className="form-control" placeholder="Latitude, Longitude (optional)" />
          <button type="button" className="btn btn-outline-secondary btn-sm" onClick={useCurrentLocation} disabled={locLoading}>{locLoading ? "Locating..." : "Use Current"}</button>
        </div>
      </div>

      <div className="mb-2">
        <label className="form-label">Address</label>
        <input value={address} onChange={e => setAddress(e.target.value)} className="form-control" placeholder="Address (optional)" />
      </div>

      <div className="mb-3">
        <label className="form-label">Remarks</label>
        <textarea value={remarks} onChange={e => setRemarks(e.target.value)} className="form-control" placeholder="Remarks (optional)"></textarea>
      </div>

      <div className="d-flex gap-2">
        <button className="btn btn-primary" disabled={loading}>{loading ? "Checking out..." : "Check Out"}</button>
        <button type="button" className="btn btn-outline-secondary" onClick={() => { setLocation(""); setAddress(""); setRemarks(""); }}>Reset</button>
      </div>
    </form>
  );
}

function RegularizationForm({ onDone, close }) {
  const [attendanceId, setAttendanceId] = useState("");
  const [reason, setReason] = useState("");
  const [requestedCheckIn, setRequestedCheckIn] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!attendanceId) return alert("Provide attendance id");
    setLoading(true);
    try {
      const payload = { attendance: Number(attendanceId), reason, requested_check_in: requestedCheckIn || null };
      const res = await apiPost("/regularizations/", payload);
      alert("Regularization requested");
      onDone && onDone(res);
      close();
    } catch (err) {
      console.error("regularize:", err);
      alert("Request failed: " + (err.message || err));
    } finally { setLoading(false); }
  }

  return (
    <form onSubmit={submit}>
      <div className="mb-2"><label className="form-label">Attendance ID</label><input className="form-control" value={attendanceId} onChange={e=>setAttendanceId(e.target.value)} placeholder="Attendance id from history" /></div>
      <div className="mb-2"><label className="form-label">Requested Check-in (ISO)</label><input className="form-control" value={requestedCheckIn} onChange={e=>setRequestedCheckIn(e.target.value)} placeholder="2025-11-01T09:00:00Z" /></div>
      <div className="mb-2"><label className="form-label">Reason</label><textarea className="form-control" value={reason} onChange={e=>setReason(e.target.value)} placeholder="Explain reason"></textarea></div>
      <div className="d-flex gap-2"><button className="btn btn-primary" disabled={loading}>{loading ? "Submitting..." : "Submit Request"}</button></div>
    </form>
  );
}

function WFHForm({ onDone, close }) {
  const [date, setDate] = useState("");
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e) {
    e.preventDefault();
    if (!date) return alert("Select date");
    setLoading(true);
    try {
      const payload = { date, reason };
      const res = await apiPost("/wfh-requests/", payload);
      alert("WFH requested");
      onDone && onDone(res);
      close();
    } catch (err) {
      console.error("wfh:", err);
      alert("Request failed: " + (err.message || err));
    } finally { setLoading(false); }
  }

  return (
    <form onSubmit={submit}>
      <div className="mb-2"><label className="form-label">Date</label><input type="date" className="form-control" value={date} onChange={e=>setDate(e.target.value)} /></div>
      <div className="mb-2"><label className="form-label">Reason</label><textarea className="form-control" value={reason} onChange={e=>setReason(e.target.value)} placeholder="Reason for WFH"></textarea></div>
      <div className="d-flex gap-2"><button className="btn btn-primary" disabled={loading}>{loading ? "Submitting..." : "Submit WFH"}</button></div>
    </form>
  );
}

/* ---------- History & Manager (unchanged) ---------- */
function HistoryList() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(()=>{ load(); }, []);
  async function load() {
    setLoading(true);
    try {
      const data = await apiGet("/attendance/my-records/");
      setRecords(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error("history:", e);
      setRecords([]);
    } finally { setLoading(false); }
  }

  return (
    <div className="container my-3">
      <h5>Attendance History</h5>
      <div className="list-group">
        {loading ? <div className="p-3 text-muted">Loading...</div> : records.length === 0 ? <div className="p-3 text-muted">No records</div> :
          records.map(r => (
            <div key={r.id || r.pk} className="list-group-item">
              <div className="d-flex justify-content-between">
                <div>
                  <strong>{dateOnly(r.date)}</strong> — <small className="muted-small">{r.shift_name}</small>
                  <div><small>In: {timeOnly(r.check_in_time)} | Out: {r.check_out_time ? timeOnly(r.check_out_time) : "-"}</small></div>
                </div>
                <div className="text-end">
                  <div><small className="muted-small">{r.status}</small></div>
                  <div><small>Work: {r.work_hours ?? "0.00"} hrs</small></div>
                  <div><small className="text-warning">Overtime: {r.overtime_hours ?? "0.00"} hrs</small></div>
                </div>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
}

function ManagerPending() {
  const [regulars, setRegulars] = useState([]);
  const [wfhs, setWfhs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(()=>{ load(); }, []);
  async function load() {
    setLoading(true);
    try {
      const [r, w] = await Promise.all([
        apiGet("/regularizations/pending-requests/").catch(()=>[]),
        apiGet("/wfh-requests/pending-requests/").catch(()=>[]),
      ]);
      setRegulars(Array.isArray(r) ? r : []);
      setWfhs(Array.isArray(w) ? w : []);
    } catch (e) { console.error("manager load:", e); setRegulars([]); setWfhs([]); } finally { setLoading(false); }
  }
  async function act(type, id, action) {
    const path = type === "reg" ? `/regularizations/${id}/${action}/` : `/wfh-requests/${id}/${action}/`;
    try { await apiPost(path, {}); alert(`${action} done`); load(); } catch (e) { console.error("approve/reject:", e); alert("Action failed"); }
  }

  return (
    <div className="container my-3">
      <h5>Manager Pending</h5>
      <div className="row">
        <div className="col-12 col-md-6">
          <h6>Regularizations</h6>
          {loading ? <div>Loading...</div> : regulars.length === 0 ? <div className="text-muted">No pending</div> : regulars.map(r => (
            <div key={r.id} className="card mb-2"><div className="card-body"><div><strong>{r.requested_by_name}</strong> — {dateOnly(r.attendance_date)}</div><div className="muted-small">{r.reason}</div><div className="mt-2"><button className="btn btn-sm btn-success me-2 px-2" onClick={()=>act("reg", r.id, "approve")}>Approve</button><button className="btn btn-sm btn-danger px-2" onClick={()=>act("reg", r.id, "reject")}>Reject</button></div></div></div>
          ))}
        </div>

        <div className="col-12 col-md-6">
          <h6>WFH Requests</h6>
          {loading ? <div>Loading...</div> : wfhs.length === 0 ? <div className="text-muted">No pending</div> : wfhs.map(w => (
            <div className="card mb-2" key={w.id}><div className="card-body"><div><strong>{w.user_name}</strong> — {dateOnly(w.date)}</div><div className="muted-small">{w.reason}</div><div className="mt-2"><button className="btn btn-sm btn-success me-2 px-2" onClick={()=>act("wfh", w.id, "approve")}>Approve</button><button className="btn btn-sm btn-danger px-2" onClick={()=>act("wfh", w.id, "reject")}>Reject</button></div></div></div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ---------------- Main Page (exports default) ---------------- */
export default function AttendancePage() {
  const [screen, setScreen] = useState("dashboard");
  const [tick, setTick] = useState(0);

  // modal state
  const [showCheckin, setShowCheckin] = useState(false);
  const [showCheckout, setShowCheckout] = useState(false);
  const [showRegularize, setShowRegularize] = useState(false);
  const [showWFH, setShowWFH] = useState(false);
  const [showMyRequests, setShowMyRequests] = useState(false);

  function refreshAll() { setTick(t => t+1); }

  // role detection & manager button visibility
  const detectedRole = getUserRole(); // lowercase string or null
  const isExplicitEmployeeOrIntern = detectedRole && (detectedRole.includes("employee") || detectedRole.includes("intern") || detectedRole === "user" || detectedRole === "staff");
  const isManagerRole = detectedRole && (detectedRole.includes("manager") || detectedRole.includes("admin") || detectedRole.includes("hr") || detectedRole.includes("super"));
  const showManagerButton = detectedRole === null ? true : isManagerRole && !isExplicitEmployeeOrIntern;

  return (
    <div className="bg-light" style={{minHeight: "100vh"}}>
      <nav className="navbar navbar-light bg-white shadow-sm">
        <div className="container">
          <a className="navbar-brand" href="#">Attendance</a>
          <div className="d-flex">
            <button className={`btn btn-sm me-2 ${screen === 'dashboard' ? 'btn-primary' : 'btn-outline-primary'}`} onClick={() => setScreen('dashboard')}>Dashboard</button>
            <button className={`btn btn-sm me-2 ${screen === 'history' ? 'btn-primary' : 'btn-outline-primary'}`} onClick={() => setScreen('history')}>History</button>
            {showManagerButton && (
              <button className={`btn btn-sm me-2 ${screen === 'manager' ? 'btn-primary' : 'btn-outline-primary'}`} onClick={() => setScreen('manager')}>Manager</button>
            )}
          </div>
        </div>
      </nav>

      <div>
        {screen === 'dashboard' && <AttendanceDashboard
          key={tick}
          onOpenCheckin={() => setShowCheckin(true)}
          onOpenCheckout={() => setShowCheckout(true)}
          onOpenHistory={() => setScreen('history')}
          onOpenRegularize={() => setShowRegularize(true)}
          onOpenWFH={() => setShowWFH(true)}
          onOpenMyRequests={() => setShowMyRequests(true)}
          refreshAll={refreshAll}
        />}

        {screen === 'checkin' && <div className="container my-3"><CheckInForm onDone={() => { refreshAll(); setScreen('dashboard'); }} close={()=>{}} /></div>}
        {screen === 'checkout' && <div className="container my-3"><CheckOutForm onDone={() => { refreshAll(); setScreen('dashboard'); }} close={()=>{}} /></div>}
        {screen === 'regularize' && <div className="container my-3"><RegularizationForm onDone={() => { refreshAll(); setScreen('dashboard'); }} close={()=>{}} /></div>}
        {screen === 'wfh' && <div className="container my-3"><WFHForm onDone={() => { refreshAll(); setScreen('dashboard'); }} close={()=>{}} /></div>}
        {screen === 'history' && <HistoryList />}
        {screen === 'manager' && <ManagerPending />}
      </div>

      {/* Modals (open from dashboard / quick actions) */}
      <Modal title="Check In" show={showCheckin} onClose={() => setShowCheckin(false)} size="modal-md">
        <CheckInForm close={() => setShowCheckin(false)} onDone={() => { refreshAll(); }} />
      </Modal>

      <Modal title="Check Out" show={showCheckout} onClose={() => setShowCheckout(false)} size="modal-md">
        <CheckOutForm close={() => setShowCheckout(false)} onDone={() => { refreshAll(); }} />
      </Modal>

      <Modal title="Request Regularization" show={showRegularize} onClose={() => setShowRegularize(false)} size="modal-md">
        <RegularizationForm close={() => setShowRegularize(false)} onDone={() => { refreshAll(); }} />
      </Modal>

      <Modal title="Request WFH" show={showWFH} onClose={() => setShowWFH(false)} size="modal-md">
        <WFHForm close={() => setShowWFH(false)} onDone={() => { refreshAll(); }} />
      </Modal>

      <MyRequests show={showMyRequests} onClose={() => setShowMyRequests(false)} refreshSignal={tick} />

      <footer className="text-center py-3 text-muted small">Attendance UI • Backend: {API_ROOT} • Ensure token in localStorage.access_token</footer>
    </div>
  );
}
