// src/components/PayrollPanel.jsx
import React, { useEffect, useState } from "react";
import {
  getMyPayroll,
  getPayrollsByEmployee,
  getAllPayrolls,
  createPayroll,
  deletePayroll,
  getSalaryStructures,
  getPayslips,
  downloadPayslip,
  getSalaryHistory,
  currencyINR,
  generatePayslips,
  approvePayslip,
  markPayslipPaid,
  getDeductions,
  createDeduction,
  patchDeduction,
  deleteDeduction,
} from "../api/payroll";
import { useAuth } from "../context/AuthContext";

// Keep same base fallback just in case (used only for direct user list fetch)
const BASE = (process.env.REACT_APP_API_BASE || "http://localhost:8000").replace(/\/$/, "");

function safeNumber(v) {
  if (v == null) return 0;
  if (typeof v === "number") return v;
  const n = parseFloat(v);
  return Number.isFinite(n) ? n : 0;
}

function extractAmounts(p) {
  const basic = safeNumber(p.basic_salary ?? p.basic ?? p.salary_structure?.basic ?? p.custom_basic ?? 0);
  const allowances = safeNumber(p.allowances ?? p.salary_structure?.allowances ?? p.custom_allowances ?? 0);
  const deductions = safeNumber(p.deductions ?? p.total_deductions ?? 0);
  const net = safeNumber(p.net_pay ?? p.net_salary ?? (basic + allowances - deductions));
  return { basic, allowances, deductions, net };
}

function formatEmployeeFallback(emp) {
  if (emp == null) return { name: "—", idDisplay: null };
  if (typeof emp === "object") {
    const user = emp.user ?? null;
    const fullName =
      emp.full_name ||
      (emp.first_name || emp.last_name ? `${(emp.first_name || "").trim()} ${(emp.last_name || "").trim()}`.trim() : null) ||
      (user ? (user.full_name || `${(user.first_name || "").trim()} ${(user.last_name || "").trim()}`.trim()) : null) ||
      emp.name ||
      emp.email ||
      null;
    const idDisplay = emp.employee_id ?? emp.employee_number ?? emp.emp_code ?? emp.id ?? emp.pk ?? null;
    return { name: fullName || `ID: ${idDisplay ?? "?"}`, idDisplay };
  }
  if (typeof emp === "string") {
    if (/^\d+$/.test(emp)) return { name: `ID: ${emp}`, idDisplay: emp };
    const m = emp.match(/\/(\d+)\/?$/);
    if (m) return { name: `ID: ${m[1]}`, idDisplay: m[1] };
    if (emp.includes("@")) return { name: emp, idDisplay: emp };
    return { name: emp, idDisplay: emp };
  }
  if (typeof emp === "number") return { name: `ID: ${emp}`, idDisplay: String(emp) };
  return { name: String(emp), idDisplay: null };
}

/* -------------------------
   Main Export
   ------------------------- */
export default function PayrollPanel() {
  const { user } = useAuth();
  const role = (user?.role || "").toLowerCase();
  const isHR = ["admin", "hr", "manager"].includes(role);
  return isHR ? <HRView user={user} /> : <EmployeeView user={user} />;
}

/* -------------------------
   HR VIEW (unchanged behavior)
   ------------------------- */
function HRView() {
  const [payrolls, setPayrolls] = useState([]);
  const [loadingPayrolls, setLoadingPayrolls] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [employees, setEmployees] = useState([]);
  const [salaryStructures, setSalaryStructures] = useState([]);
  const [loadingEmployees, setLoadingEmployees] = useState(false);
  const [payrollForm, setPayrollForm] = useState({ employee: "", salary_structure: "", effective_from: "", is_active: true });
  const [payslips, setPayslips] = useState([]);
  const [loadingPayslips, setLoadingPayslips] = useState(false);
  const [generateModalOpen, setGenerateModalOpen] = useState(false);
  const [generateForm, setGenerateForm] = useState({ month: "", year: "", employeeIds: "", employeeSelection: [], forAll: false, totalWorkingDays: 26 });
  const [markPaidModal, setMarkPaidModal] = useState({ open: false, payslip: null, paymentDate: "", paymentMode: "", reference: "" });
  const [deductionModalOpen, setDeductionModalOpen] = useState(false);
  const [deductionPayload, setDeductionPayload] = useState({ employee: "", deduction_type: "LOAN", description: "", total_amount: "", installment_amount: "", remaining_amount: "", start_month: "", start_year: "", end_month: "", end_year: "" });
  const [deductions, setDeductions] = useState([]);
  const [loadingDeductions, setLoadingDeductions] = useState(false);
  const [history, setHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    loadAllData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadAllData = async () => {
    await Promise.all([loadPayrolls(), loadEmployees(), loadSalaryStructures(), loadPayslips(), loadDeductions(), loadHistory()]);
  };

  const loadPayrolls = async () => {
    setLoadingPayrolls(true);
    try {
      const data = await getAllPayrolls();
      setPayrolls(Array.isArray(data) ? data : []);
    } catch (err) {
      alert(err?.message || "Failed to load payrolls");
      setPayrolls([]);
    } finally {
      setLoadingPayrolls(false);
    }
  };

  const loadEmployees = async () => {
    setLoadingEmployees(true);
    try {
      // Fetch employee profiles instead of users directly
      const res = await fetch(`${BASE}/api/hr/employees/`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token") || localStorage.getItem("access") || localStorage.getItem("token") || localStorage.getItem("auth_token")}`,
          "Content-Type": "application/json",
        },
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        alert(`Failed to load employees: ${res.status} ${res.statusText} ${text ? "- " + text : ""}`);
        setEmployees([]);
        setLoadingEmployees(false);
        return;
      }
      const profileData = await res.json();
      let profiles = [];
      if (Array.isArray(profileData)) profiles = profileData;
      else if (profileData.results && Array.isArray(profileData.results)) profiles = profileData.results;
      else if (profileData.data && Array.isArray(profileData.data)) profiles = profileData.data;
      
      const transformed = profiles.map((p) => ({
        id: p.id ?? p.pk, // EmployeeProfile ID
        user_id: p.user?.id ?? p.user_id, // User ID
        employee_id: p.employee_id ?? `EP-${p.id}`,
        first_name: p.user?.first_name ?? p.first_name ?? "",
        last_name: p.user?.last_name ?? p.last_name ?? "",
        full_name: p.user?.full_name ?? p.full_name ?? `${(p.user?.first_name || p.first_name || "").trim()} ${(p.user?.last_name || p.last_name || "").trim()}`.trim(),
        email: p.user?.email ?? p.email ?? "",
        raw: p,
      }));
      console.log('[loadEmployees] Loaded employee profiles:', transformed);
      setEmployees(transformed);
    } catch (err) {
      alert(err?.message || "Failed to load employees");
      setEmployees([]);
    } finally {
      setLoadingEmployees(false);
    }
  };

  const loadSalaryStructures = async () => {
    try {
      const data = await getSalaryStructures();
      setSalaryStructures(Array.isArray(data) ? data : []);
    } catch (err) {
      alert(err?.message || "Failed to load salary structures");
      setSalaryStructures([]);
    }
  };

  const loadPayslips = async () => {
    setLoadingPayslips(true);
    try {
      const data = await getPayslips();
      setPayslips(Array.isArray(data) ? data : []);
    } catch (err) {
      alert(err?.message || "Failed to load payslips");
      setPayslips([]);
    } finally {
      setLoadingPayslips(false);
    }
  };

  const loadDeductions = async () => {
    setLoadingDeductions(true);
    try {
      const data = await getDeductions();
      setDeductions(Array.isArray(data) ? data : []);
    } catch (err) {
      alert(err?.message || "Failed to load deductions");
      setDeductions([]);
    } finally {
      setLoadingDeductions(false);
    }
  };

  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const data = await getSalaryHistory();
      setHistory(Array.isArray(data) ? data : []);
    } catch (err) {
      alert(err?.message || "Failed to load salary history");
      setHistory([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const resolveEmployee = (maybeObjOrId) => {
    if (maybeObjOrId && typeof maybeObjOrId === "object") {
      const name = maybeObjOrId.full_name || maybeObjOrId.name || maybeObjOrId.email || `${maybeObjOrId.first_name || ""} ${maybeObjOrId.last_name || ""}`.trim();
      const idDisplay = maybeObjOrId.employee_id ?? maybeObjOrId.id ?? maybeObjOrId.pk ?? null;
      return { name: name || (idDisplay ? `ID: ${idDisplay}` : "—"), idDisplay };
    }
    const idStr = typeof maybeObjOrId === "number" ? String(maybeObjOrId) : (typeof maybeObjOrId === "string" ? maybeObjOrId : null);
    if (idStr) {
      const found = employees.find((e) => String(e.id) === idStr || String(e.employee_id) === idStr || String(e.raw?.id) === idStr || String(e.raw?.pk) === idStr);
      if (found) return { name: found.full_name || found.email || `ID: ${found.employee_id}`, idDisplay: found.employee_id ?? found.id };
    }
    return formatEmployeeFallback(maybeObjOrId);
  };

  const openAddPayroll = () => {
    setPayrollForm({ employee: "", salary_structure: "", effective_from: "", is_active: true });
    setModalOpen(true);
  };

  const handleCreatePayroll = async (e) => {
    e.preventDefault();
    const basePayload = { employee: payrollForm.employee, salary_structure: payrollForm.salary_structure, effective_from: payrollForm.effective_from, is_active: !!payrollForm.is_active };
    const payload = {
      employee: Number.isFinite(Number(basePayload.employee)) ? Number(basePayload.employee) : basePayload.employee,
      salary_structure: Number(basePayload.salary_structure),
      effective_from: basePayload.effective_from,
      is_active: basePayload.is_active,
    };
    try {
      const res = await createPayroll(payload);
      setModalOpen(false);
      await loadPayrolls();
      alert(res?.detail || "Payroll saved successfully");
    } catch (err) {
      if (err?.body) {
        try {
          const b = typeof err.body === "string" ? JSON.parse(err.body) : err.body;
          alert(JSON.stringify(b));
          return;
        } catch (e) {
          alert(typeof err.body === "string" ? err.body : JSON.stringify(err.body));
          return;
        }
      }
      alert(err?.message || "Failed to create payroll");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete payroll?")) return;
    try {
      await deletePayroll(id);
      await loadPayrolls();
    } catch (err) {
      if (err?.body && typeof err.body === "string" && err.body.includes("ProtectedError")) {
        alert("Cannot delete payroll: related payslips exist. Delete related payslips first or mark them accordingly.");
        return;
      }
      alert(err?.message || "Failed to delete payroll.");
    }
  };

  const handleGeneratePayslips = async (e) => {
    e.preventDefault();
    const month = Number(generateForm.month);
    const year = Number(generateForm.year);
    if (!Number.isInteger(month) || month < 1 || month > 12) return alert("Please enter a valid month (1-12).");
    if (!Number.isInteger(year) || year < 2000 || year > 2100) return alert("Please enter a valid year.");
    try {
      let employeeIds = [];
      if (Array.isArray(generateForm.employeeSelection) && generateForm.employeeSelection.length > 0) {
        employeeIds = generateForm.employeeSelection.map((v) => Number(v)).filter((n) => Number.isFinite(n) && n > 0);
      }
      if (!generateForm.forAll && (generateForm.employeeIds || "").trim() !== "" && employeeIds.length === 0) {
        const matches = (generateForm.employeeIds || "").match(/\d+/g) || [];
        employeeIds = matches.map((m) => Number(m)).filter((n) => Number.isFinite(n) && n > 0);
      }
      if (!generateForm.forAll && !(employeeIds && employeeIds.length > 0)) return alert('Either check "Generate for all employees" or provide employee IDs (or use the multi-select).');
      const payload = { month, year, total_working_days: Number(generateForm.totalWorkingDays) || 26 };
      if (!generateForm.forAll) payload.employee_ids = employeeIds;
      const res = await generatePayslips(payload);
      setGenerateModalOpen(false);
      await loadPayslips();
      alert(res?.detail || "Payslips generated");
    } catch (err) {
      if (err?.body) {
        try {
          const body = typeof err.body === "string" ? JSON.parse(err.body) : err.body;
          alert(JSON.stringify(body));
        } catch (e) {
          alert(typeof err.body === "string" ? err.body : JSON.stringify(err.body));
        }
      } else {
        alert(err?.message || "Failed to generate payslips");
      }
    }
  };

  const handleApprovePayslip = async (id) => {
    setPayslips((prev) => prev.map((ps) => (String(ps.id ?? ps.pk) === String(id) ? { ...ps, status: "APPROVED" } : ps)));
    try {
      await approvePayslip(id);
      await loadPayslips();
      alert("Payslip approved");
    } catch (err) {
      alert(err?.message || "Failed to approve payslip");
      await loadPayslips();
    }
  };

  const openMarkPaid = (p) => setMarkPaidModal({ open: true, payslip: p, paymentDate: "", paymentMode: "", reference: "" });

  const handleMarkPaid = async (e) => {
    e.preventDefault();
    const { payslip, paymentDate, paymentMode, reference } = markPaidModal;
    if (!payslip) return;
    const id = payslip.id ?? payslip.pk;
    setPayslips((prev) => prev.map((ps) => (String(ps.id ?? ps.pk) === String(id) ? { ...ps, is_paid: true, status: "PAID" } : ps)));
    try {
      await markPayslipPaid(id, { paymentDate, paymentMode, reference });
      setMarkPaidModal({ open: false, payslip: null, paymentDate: "", paymentMode: "", reference: "" });
      await loadPayslips();
      alert("Marked as paid");
    } catch (err) {
      alert(err?.message || "Failed to mark payslip as paid");
      await loadPayslips();
    }
  };

  const openCreateDeduction = () => {
    setDeductionPayload({ employee: "", deduction_type: "LOAN", description: "", total_amount: "", installment_amount: "", remaining_amount: "", start_month: "", start_year: "", end_month: "", end_year: "" });
    setDeductionModalOpen(true);
  };

  const handleCreateDeduction = async (e) => {
    e.preventDefault();
    try {
      const p = deductionPayload;
      const selectedEmployee = employees.find(emp => String(emp.id) === String(p.employee));
      console.log('[Deduction] All employees:', employees);
      console.log('[Deduction] Selected employee from dropdown:', selectedEmployee);
      console.log('[Deduction] Raw employee value from form:', p.employee);
      console.log('[Deduction] Selected employee details:', {
        profileId: selectedEmployee?.id,
        userId: selectedEmployee?.user_id,
        employeeId: selectedEmployee?.employee_id,
        email: selectedEmployee?.email,
        name: selectedEmployee?.full_name
      });
      
      const payload = {
        employee: !isNaN(Number(p.employee)) ? Number(p.employee) : p.employee,
        deduction_type: p.deduction_type,
        description: p.description,
        total_amount: Number(p.total_amount),
        installment_amount: Number(p.installment_amount),
        remaining_amount: p.remaining_amount !== "" ? Number(p.remaining_amount) : Number(p.total_amount),
        start_month: Number(p.start_month),
        start_year: Number(p.start_year),
        end_month: Number(p.end_month),
        end_year: Number(p.end_year),
      };
      console.log('[Deduction] Final payload being sent to API:', payload);
      await createDeduction(payload);
      setDeductionModalOpen(false);
      setDeductionPayload({});
      await loadDeductions();
      alert("Deduction created");
    } catch (err) {
      console.error('[Deduction] Error creating deduction:', err);
      alert(err?.message || "Failed to create deduction");
    }
  };

  const handleDeleteDeduction = async (id) => {
    if (!window.confirm("Delete deduction?")) return;
    try {
      await deleteDeduction(id);
      await loadDeductions();
    } catch (err) {
      alert(err?.message || "Failed to delete deduction");
    }
  };

  const handleMarkDeductionComplete = async (d) => {
    const remaining = Number(d.remaining_amount ?? d.total_amount ?? 0);
    if (!window.confirm(`Mark this deduction as complete? Remaining amount: ${currencyINR(remaining)} — this will set remaining_amount to 0.`)) return;
    try {
      await patchDeduction(d.id ?? d.pk, { remaining_amount: 0 });
      await loadDeductions();
    } catch (err) {
      alert(err?.message || "Failed to update deduction");
    }
  };

  /* ---------- small summary values for UI cards ---------- */
  const summary = {
    payrolls: payrolls.length,
    payslips: payslips.length,
    payslipsPending: payslips.filter((p) => !p.is_paid && (String((p.status ?? "").toUpperCase()) !== "APPROVED")).length,
    deductionsActive: deductions.filter((d) => Number(d.remaining_amount ?? d.total_amount ?? 0) > 0).length,
    history: history.length,
  };

  return (
    <div className="container my-3">
      {/* Header + Actions */}
      <div className="d-flex flex-column flex-md-row justify-content-between align-items-start gap-3 mb-3">
        <div>
          <h2 className="mb-1">Payroll Administration</h2>
          <div className="text-muted">Manage salary structures, assignments, payslips and deductions.</div>
        </div>
        <div className="d-flex gap-2">
          <button className="btn btn-primary" onClick={() => openAddPayroll()}>+ Add Payroll</button>
          <button className="btn btn-outline-secondary" onClick={() => setGenerateModalOpen(true)}>Generate Payslips</button>
          <button className="btn btn-outline-warning" onClick={() => openCreateDeduction()}>Create Deduction</button>
          <button className="btn btn-outline-info" onClick={() => loadAllData()}>Refresh</button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="row g-3 mb-4">
        <div className="col-6 col-md-3">
          <div className="card shadow-sm">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-start">
                <div>
                  <small className="text-muted">Payrolls</small>
                  <h4 className="mt-1">{summary.payrolls}</h4>
                </div>
                <div className="text-end">
                  <small className="badge bg-secondary">All</small>
                </div>
              </div>
              <div className="mt-2 small text-muted">Assigned salary records</div>
            </div>
          </div>
        </div>

        <div className="col-6 col-md-3">
          <div className="card shadow-sm">
            <div className="card-body">
              <small className="text-muted">Payslips</small>
              <h4 className="mt-1">{summary.payslips}</h4>
              <div className="mt-2 small text-muted">{summary.payslipsPending} pending approvals</div>
            </div>
          </div>
        </div>

        <div className="col-6 col-md-3">
          <div className="card shadow-sm">
            <div className="card-body">
              <small className="text-muted">Deductions</small>
              <h4 className="mt-1">{summary.deductionsActive}</h4>
              <div className="mt-2 small text-muted">Active deductions</div>
            </div>
          </div>
        </div>

        <div className="col-6 col-md-3">
          <div className="card shadow-sm">
            <div className="card-body">
              <small className="text-muted">History</small>
              <h4 className="mt-1">{summary.history}</h4>
              <div className="mt-2 small text-muted">Salary changes</div>
            </div>
          </div>
        </div>
      </div>

      {/* Payroll table */}
      <div className="card mb-4">
        <div className="card-header d-flex justify-content-between align-items-center">
          <strong>Salary Assignments</strong>
          <div>
            <button className="btn btn-sm btn-outline-secondary me-2" onClick={() => loadPayrolls()}>Refresh</button>
            <button className="btn btn-sm btn-outline-primary" onClick={() => openAddPayroll()}>Add</button>
          </div>
        </div>
        <div className="card-body p-0">
          {loadingPayrolls ? (
            <div className="p-4 text-center">
              <div className="spinner-border" role="status" />
            </div>
          ) : payrolls.length === 0 ? (
            <div className="p-4 text-center text-muted">No payroll records found — create one using the button above.</div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover table-sm mb-0">
                <thead className="table-light">
                  <tr>
                    <th>ID</th>
                    <th>Employee</th>
                    <th>Structure</th>
                    <th>Basic</th>
                    <th>Gross</th>
                    <th>Effective</th>
                    <th>Active</th>
                    <th className="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {payrolls.map((p) => {
                    const structName = p.salary_structure_name ?? `ID: ${p.salary_structure ?? "?"}`;
                    const basicSalary = p.basic_salary ?? p.custom_basic ?? p.salary_structure?.basic ?? 0;
                    const grossSalary = p.gross_salary ?? (basicSalary + (p.allowances ?? 0));
                    return (
                      <tr key={p.id ?? p.pk}>
                        <td>{p.id ?? p.pk}</td>
                        <td>
                          <div className="fw-semibold">{p.employee_name || "—"}</div>
                          <small className="text-muted">{p.employee_id ? `Emp: ${p.employee_id}` : ""}</small>
                        </td>
                        <td>{structName}</td>
                        <td>{currencyINR(basicSalary)}</td>
                        <td>{currencyINR(grossSalary)}</td>
                        <td>{p.effective_from || "—"}</td>
                        <td><span className={`badge ${p.is_active ? "bg-success" : "bg-secondary"}`}>{p.is_active ? "Active" : "Inactive"}</span></td>
                        <td className="text-end">
                          <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(p.id ?? p.pk)}>Delete</button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Payslips */}
      <div className="card mb-4">
        <div className="card-header d-flex justify-content-between align-items-center">
          <strong>Payslips</strong>
          <div>
            <button className="btn btn-sm btn-outline-secondary me-2" onClick={() => loadPayslips()}>Refresh</button>
            <button className="btn btn-sm btn-primary" onClick={() => setGenerateModalOpen(true)}>Generate</button>
          </div>
        </div>
        <div className="card-body p-0">
          {loadingPayslips ? (
            <div className="p-4 text-center"><div className="spinner-border" /></div>
          ) : payslips.length === 0 ? (
            <div className="p-4 text-center text-muted">No payslips yet.</div>
          ) : (
            <div className="table-responsive">
              <table className="table table-sm mb-0">
                <thead className="table-light">
                  <tr>
                    <th>ID</th>
                    <th>Employee</th>
                    <th>Period</th>
                    <th>Status</th>
                    <th className="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {payslips.map((p) => {
                    const statusStr = String((p.status ?? "").toUpperCase() || "");
                    const isPaid = !!p.is_paid || statusStr === "PAID";
                    const isApproved = statusStr === "APPROVED";
                    const displayStatus = isPaid ? "PAID" : (p.status ?? "GENERATED");
                    return (
                      <tr key={p.id ?? p.pk}>
                        <td>{p.id ?? p.pk}</td>
                        <td>
                          <div className="fw-semibold">{p.employee_name || "—"}</div>
                          <small className="text-muted">{p.employee_id ? `Emp: ${p.employee_id}` : ""} {p.employee_email || ""}</small>
                        </td>
                        <td>{p.month ?? p.period ?? "—"}</td>
                        <td><span className={`badge ${isPaid ? "bg-success" : (isApproved ? "bg-info" : "bg-secondary")}`}>{displayStatus}</span></td>
                        <td className="text-end">
                          <button className="btn btn-sm btn-outline-primary me-1" onClick={async () => {
                            try {
                              const { blob, filename } = await downloadPayslip(p.id ?? p.pk);
                              const url = window.URL.createObjectURL(blob);
                              const a = document.createElement("a");
                              a.href = url;
                              a.download = filename;
                              document.body.appendChild(a);
                              a.click();
                              a.remove();
                              window.URL.revokeObjectURL(url);
                            } catch (err) {
                              alert(err?.message || "Failed to download");
                            }
                          }}>Download</button>

                          <button
                            className="btn btn-sm btn-success me-1"
                            onClick={() => handleApprovePayslip(p.id ?? p.pk)}
                            disabled={isPaid || isApproved}
                          >
                            Approve
                          </button>

                          <button
                            className="btn btn-sm btn-warning"
                            onClick={() => openMarkPaid(p)}
                            disabled={isPaid}
                          >
                            Mark Paid
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Deductions */}
      <div className="card mb-4">
        <div className="card-header d-flex justify-content-between align-items-center">
          <strong>Deductions</strong>
          <div>
            <button className="btn btn-sm btn-outline-secondary me-2" onClick={() => loadDeductions()}>Refresh</button>
            <button className="btn btn-sm btn-outline-warning" onClick={() => openCreateDeduction()}>Create</button>
          </div>
        </div>
        <div className="card-body p-0">
          {loadingDeductions ? (
            <div className="p-4 text-center"><div className="spinner-border" /></div>
          ) : deductions.length === 0 ? (
            <div className="p-4 text-center text-muted">No deductions found.</div>
          ) : (
            <div className="table-responsive">
              <table className="table table-sm mb-0">
                <thead className="table-light">
                  <tr>
                    <th>ID</th>
                    <th>Employee</th>
                    <th>Type</th>
                    <th>Total</th>
                    <th>Installment</th>
                    <th>Remaining</th>
                    <th>Period</th>
                    <th>Status</th>
                    <th className="text-end">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {deductions.map((d) => {
                    const status = Number(d.remaining_amount) <= 0 ? "Completed" : "Active";
                    const start = d.start_month ? `${d.start_month}/${d.start_year ?? ""}` : "—";
                    const end = d.end_month ? `${d.end_month}/${d.end_year ?? ""}` : "—";
                    const empDisplay = d.employee_name || d.employee_id || `ID: ${d.employee}`;
                    return (
                      <tr key={d.id ?? d.pk}>
                        <td>{d.id ?? d.pk}</td>
                        <td>
                          {d.employee_id && <span className="badge bg-secondary me-1">{d.employee_id}</span>}
                          {d.employee_name || "—"}
                        </td>
                        <td>{d.deduction_type ?? d.type ?? "—"}</td>
                        <td>{currencyINR(d.total_amount ?? d.amount ?? 0)}</td>
                        <td>{currencyINR(d.installment_amount ?? 0)}</td>
                        <td>{currencyINR(d.remaining_amount ?? 0)}</td>
                        <td>{start} - {end}</td>
                        <td><span className={`badge ${status === "Completed" ? "bg-success" : "bg-secondary"}`}>{status}</span></td>
                        <td className="text-end">
                          {Number(d.remaining_amount) > 0 && <button className="btn btn-sm btn-success me-1" onClick={() => handleMarkDeductionComplete(d)}>Mark Complete</button>}
                          <button className="btn btn-sm btn-danger" onClick={() => handleDeleteDeduction(d.id ?? d.pk)}>Delete</button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Salary History (HR) */}
      <div className="card mb-4">
        <div className="card-header d-flex justify-content-between align-items-center">
          <strong>Salary History</strong>
          <div>
            <button className="btn btn-sm btn-outline-secondary" onClick={() => loadHistory()}>Refresh</button>
          </div>
        </div>
        <div className="card-body p-0">
          {loadingHistory ? (
            <div className="p-4 text-center"><div className="spinner-border" /></div>
          ) : history.length === 0 ? (
            <div className="p-4 text-center text-muted">No salary history entries.</div>
          ) : (
            <div className="table-responsive">
              <table className="table table-sm mb-0">
                <thead className="table-light">
                  <tr>
                    <th>ID</th>
                    <th>Employee</th>
                    <th>Type</th>
                    <th>Effective</th>
                    <th>Basic</th>
                    <th>Net</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => {
                    const empResolved = resolveEmployee(h.employee ?? h.employee_id ?? h.user ?? null);
                    const amounts = extractAmounts(h);
                    return (
                      <tr key={h.id ?? h.pk}>
                        <td>{h.id ?? h.pk}</td>
                        <td>{empResolved.name}</td>
                        <td>{h.change_type ?? h.note ?? "—"}</td>
                        <td>{h.effective_date ?? h.effective_from ?? "—"}</td>
                        <td>{currencyINR(amounts.basic)}</td>
                        <td>{currencyINR(amounts.net)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* ---------- Modals (kept same behavior) ---------- */}

      {/* Create Payroll Modal */}
      {modalOpen && (
        <div className="modal fade show d-block" style={{ backgroundColor: "rgba(0,0,0,0.45)" }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <form onSubmit={handleCreatePayroll}>
                <div className="modal-header">
                  <h5 className="modal-title">Add Payroll</h5>
                  <button type="button" className="btn-close" onClick={() => setModalOpen(false)} />
                </div>
                <div className="modal-body">
                  <div className="row g-3">
                    <div className="col-12">
                      <label className="form-label">Employee <span className="text-danger">*</span></label>
                      {loadingEmployees ? (
                        <div className="form-control">Loading employees...</div>
                      ) : (
                        <select required className="form-select" value={payrollForm.employee} onChange={(e) => setPayrollForm({ ...payrollForm, employee: e.target.value })}>
                          <option value="">-- Select Employee --</option>
                          {employees.length === 0 && <option value="" disabled>No employees found</option>}
                          {employees.map((emp) => (
                            <option key={emp.id} value={emp.id}>{emp.employee_id} — {emp.full_name || emp.email}</option>
                          ))}
                        </select>
                      )}
                      <div className="form-text">Choose the user to assign salary (showing all users).</div>
                    </div>

                    <div className="col-12">
                      <label className="form-label">Salary Structure <span className="text-danger">*</span></label>
                      <select required className="form-select" value={payrollForm.salary_structure} onChange={(e) => setPayrollForm({ ...payrollForm, salary_structure: e.target.value })}>
                        <option value="">-- Select Salary Structure --</option>
                        {salaryStructures.map((struct) => (
                          <option key={struct.id} value={struct.id}>{struct.name} {struct.designation ? `- ${struct.designation}` : ""} ({currencyINR(struct.basic_salary ?? struct.basic ?? 0)})</option>
                        ))}
                      </select>
                      <div className="form-text">Select template to assign to the employee.</div>
                    </div>

                    <div className="col-md-6">
                      <label className="form-label">Effective From <span className="text-danger">*</span></label>
                      <input type="date" required className="form-control" value={payrollForm.effective_from} onChange={(e) => setPayrollForm({ ...payrollForm, effective_from: e.target.value })} />
                    </div>

                    <div className="col-md-6">
                      <label className="form-label">Active</label>
                      <select className="form-select" value={String(payrollForm.is_active)} onChange={(e) => setPayrollForm({ ...payrollForm, is_active: e.target.value === "true" })}>
                        <option value="true">Active</option>
                        <option value="false">Inactive</option>
                      </select>
                    </div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-outline-secondary" onClick={() => setModalOpen(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary">Save</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Generate Modal */}
      {generateModalOpen && (
        <div className="modal fade show d-block" style={{ backgroundColor: "rgba(0,0,0,0.45)" }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <form onSubmit={handleGeneratePayslips}>
                <div className="modal-header">
                  <h5 className="modal-title">Generate Payslips</h5>
                  <button type="button" className="btn-close" onClick={() => setGenerateModalOpen(false)} />
                </div>
                <div className="modal-body">
                  <div className="mb-2">
                    <label className="form-label">Month (1-12)</label>
                    <input required type="number" min="1" max="12" className="form-control" value={generateForm.month} onChange={(e) => setGenerateForm({ ...generateForm, month: e.target.value })} />
                  </div>
                  <div className="mb-2">
                    <label className="form-label">Year</label>
                    <input required type="number" min="2000" max="2100" className="form-control" value={generateForm.year} onChange={(e) => setGenerateForm({ ...generateForm, year: e.target.value })} />
                  </div>
                  <div className="mb-2 form-check">
                    <input id="forAll" type="checkbox" className="form-check-input" checked={generateForm.forAll} onChange={(e) => setGenerateForm({ ...generateForm, forAll: e.target.checked })} />
                    <label className="form-check-label" htmlFor="forAll">Generate for all employees</label>
                  </div>
                  <div className="mb-2">
                    <label className="form-label">Select Employees (optional)</label>
                    <select multiple className="form-select" value={generateForm.employeeSelection} onChange={(e) => { const vals = Array.from(e.target.selectedOptions).map((o) => o.value); setGenerateForm({ ...generateForm, employeeSelection: vals }); }} disabled={generateForm.forAll}>
                      {employees.map((emp) => (
                        <option key={emp.id} value={emp.id}>{emp.employee_id} — {emp.full_name || emp.email}</option>
                      ))}
                    </select>
                    <div className="form-text">Hold Ctrl/Cmd to select multiple.</div>
                  </div>
                  <div className="mb-2">
                    <label className="form-label">Employee IDs (comma separated)</label>
                    <input type="text" className="form-control" placeholder="e.g. 2,3,4" value={generateForm.employeeIds} onChange={(e) => setGenerateForm({ ...generateForm, employeeIds: e.target.value })} disabled={generateForm.forAll} />
                  </div>
                  <div className="mb-2">
                    <label className="form-label">Total working days</label>
                    <input type="number" min="1" max="31" className="form-control" value={generateForm.totalWorkingDays} onChange={(e) => setGenerateForm({ ...generateForm, totalWorkingDays: e.target.value })} />
                    <div className="form-text">Defaults to 26 if left blank.</div>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-outline-secondary" onClick={() => setGenerateModalOpen(false)}>Cancel</button>
                  <button type="submit" className="btn btn-primary">Generate</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Mark Paid Modal */}
      {markPaidModal.open && (
        <div className="modal fade show d-block" style={{ backgroundColor: "rgba(0,0,0,0.45)" }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <form onSubmit={handleMarkPaid}>
                <div className="modal-header">
                  <h5 className="modal-title">Mark Payslip Paid</h5>
                  <button type="button" className="btn-close" onClick={() => setMarkPaidModal({ open: false, payslip: null, paymentDate: "", paymentMode: "", reference: "" })} />
                </div>
                <div className="modal-body">
                  <div className="mb-2">
                    <label className="form-label">Payment Date</label>
                    <input type="date" className="form-control" value={markPaidModal.paymentDate} onChange={(e) => setMarkPaidModal({ ...markPaidModal, paymentDate: e.target.value })} required />
                  </div>
                  <div className="mb-2">
                    <label className="form-label">Payment Mode</label>
                    <input type="text" className="form-control" value={markPaidModal.paymentMode} onChange={(e) => setMarkPaidModal({ ...markPaidModal, paymentMode: e.target.value })} required />
                  </div>
                  <div className="mb-2">
                    <label className="form-label">Reference</label>
                    <input type="text" className="form-control" value={markPaidModal.reference} onChange={(e) => setMarkPaidModal({ ...markPaidModal, reference: e.target.value })} />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-outline-secondary" onClick={() => setMarkPaidModal({ open: false, payslip: null, paymentDate: "", paymentMode: "", reference: "" })}>Cancel</button>
                  <button type="submit" className="btn btn-primary">Mark Paid</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Deduction modal */}
      {deductionModalOpen && (
        <div className="modal fade show d-block" style={{ backgroundColor: "rgba(0,0,0,0.45)" }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <form onSubmit={handleCreateDeduction}>
                <div className="modal-header">
                  <h5 className="modal-title">Create Deduction</h5>
                  <button type="button" className="btn-close" onClick={() => { setDeductionModalOpen(false); setDeductionPayload({}); }} />
                </div>
                <div className="modal-body">
                  <div className="row g-3">
                    <div className="col-12">
                      <label className="form-label">Employee</label>
                      {loadingEmployees ? (
                        <div className="form-control">Loading employees...</div>
                      ) : (
                        <select required className="form-select" value={deductionPayload.employee} onChange={(e) => setDeductionPayload({ ...deductionPayload, employee: e.target.value })}>
                          <option value="">-- Select Employee --</option>
                          {employees.map((emp) => (
                            <option key={emp.id} value={emp.id}>{emp.employee_id} — {emp.full_name || emp.email}</option>
                          ))}
                        </select>
                      )}
                    </div>

                    <div className="col-md-6">
                      <label className="form-label">Deduction Type</label>
                      <select required className="form-select" value={deductionPayload.deduction_type} onChange={(e) => setDeductionPayload({ ...deductionPayload, deduction_type: e.target.value })}>
                        <option value="LOAN">LOAN</option>
                        <option value="ADVANCE">ADVANCE</option>
                        <option value="OTHER">OTHER</option>
                      </select>
                    </div>

                    <div className="col-md-6">
                      <label className="form-label">Total Amount</label>
                      <input required type="number" step="0.01" className="form-control" value={deductionPayload.total_amount} onChange={(e) => setDeductionPayload({ ...deductionPayload, total_amount: e.target.value })} />
                    </div>

                    <div className="col-md-6">
                      <label className="form-label">Installment Amount</label>
                      <input required type="number" step="0.01" className="form-control" value={deductionPayload.installment_amount} onChange={(e) => setDeductionPayload({ ...deductionPayload, installment_amount: e.target.value })} />
                    </div>

                    <div className="col-md-6">
                      <label className="form-label">Remaining Amount (optional)</label>
                      <input type="number" step="0.01" className="form-control" value={deductionPayload.remaining_amount} onChange={(e) => setDeductionPayload({ ...deductionPayload, remaining_amount: e.target.value })} placeholder="defaults to total amount if left blank" />
                    </div>

                    <div className="col-12">
                      <label className="form-label">Description</label>
                      <textarea required className="form-control" rows="3" value={deductionPayload.description} onChange={(e) => setDeductionPayload({ ...deductionPayload, description: e.target.value })} />
                    </div>

                    <div className="col-md-3">
                      <label className="form-label">Start Month (1-12)</label>
                      <input required type="number" min="1" max="12" className="form-control" value={deductionPayload.start_month} onChange={(e) => setDeductionPayload({ ...deductionPayload, start_month: e.target.value })} />
                    </div>

                    <div className="col-md-3">
                      <label className="form-label">Start Year</label>
                      <input required type="number" min="1900" max="2100" className="form-control" value={deductionPayload.start_year} onChange={(e) => setDeductionPayload({ ...deductionPayload, start_year: e.target.value })} />
                    </div>

                    <div className="col-md-3">
                      <label className="form-label">End Month (1-12)</label>
                      <input required type="number" min="1" max="12" className="form-control" value={deductionPayload.end_month} onChange={(e) => setDeductionPayload({ ...deductionPayload, end_month: e.target.value })} />
                    </div>

                    <div className="col-md-3">
                      <label className="form-label">End Year</label>
                      <input required type="number" min="1900" max="2100" className="form-control" value={deductionPayload.end_year} onChange={(e) => setDeductionPayload({ ...deductionPayload, end_year: e.target.value })} />
                    </div>
                  </div>
                </div>

                <div className="modal-footer">
                  <button type="button" className="btn btn-outline-secondary" onClick={() => { setDeductionModalOpen(false); setDeductionPayload({}); }}>Cancel</button>
                  <button type="submit" className="btn btn-primary">Create</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* -------------------------
   EMPLOYEE VIEW
   Fixed: ensure numeric employee id passed to payslips/deductions/history queries
   (keeps same functionality otherwise)
   ------------------------- */
function EmployeeView({ user }) {
  const [payroll, setPayroll] = useState(null);
  const [loadingPayroll, setLoadingPayroll] = useState(true);
  const [payslips, setPayslips] = useState([]);
  const [deductions, setDeductions] = useState([]);
  const [history, setHistory] = useState([]);
  const [activeTab, setActiveTab] = useState("current");
  const [downloading, setDownloading] = useState(false);
  const [loadingPayslips, setLoadingPayslips] = useState(false);
  const [loadingDeductions, setLoadingDeductions] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    loadPayroll();
    loadPayslips();
    loadDeductions();
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, user?.pk]);

  // helper: return numeric id if available, otherwise null
  const resolveNumericUserId = () => {
    const maybe = user ?? {};
    // common places
    const candidates = [maybe.id ?? maybe.pk, maybe.user_id, maybe.raw?.id, maybe.raw?.pk];
    for (const c of candidates) {
      if (c == null) continue;
      if (typeof c === "number" && Number.isFinite(c)) return c;
      if (typeof c === "string" && /^\d+$/.test(c)) return Number(c);
    }
    return null;
  };

  const loadPayroll = async () => {
    setLoadingPayroll(true);
    try {
      const userId = resolveNumericUserId();
      if (userId) {
        const arr = await getPayrollsByEmployee(userId);
        if (Array.isArray(arr) && arr.length > 0) {
          const active = arr.find((r) => r.is_active || r.active) ?? null;
          if (active) { setPayroll(active); setLoadingPayroll(false); return; }
          const withDate = arr.filter((a) => a.effective_from).sort((a,b) => new Date(b.effective_from) - new Date(a.effective_from));
          setPayroll(withDate.length ? withDate[0] : arr[0]);
          setLoadingPayroll(false);
          return;
        }
      }
      try {
        const mine = await getMyPayroll();
        if (mine) setPayroll(mine); else setPayroll(null);
      } catch (err) {
        if (err && (err.status === 401 || err.status === 403)) throw err;
        setPayroll(null);
      }
    } catch (err) {
      alert(err?.message || "Failed to load payroll");
      setPayroll(null);
    } finally { setLoadingPayroll(false); }
  };

  const loadPayslips = async () => {
    setLoadingPayslips(true);
    try {
      const userId = resolveNumericUserId();
      console.log('[EmployeeView] Loading payslips for userId:', userId);
      // pass numeric id only. If no numeric id, call without employee filter (backend should return current user's payslips)
      const data = userId ? await getPayslips({ employee: userId }) : await getPayslips();
      console.log('[EmployeeView] Payslips received:', data);
      setPayslips(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('[EmployeeView] Failed to load payslips:', err);
      alert(err?.message || "Failed to load payslips");
      setPayslips([]);
    } finally { setLoadingPayslips(false); }
  };

  const loadDeductions = async () => {
    setLoadingDeductions(true);
    try {
      const userId = resolveNumericUserId();
      console.log('[EmployeeView] Loading deductions for userId:', userId);
      const data = userId ? await getDeductions({ employee: userId }) : await getDeductions();
      console.log('[EmployeeView] Deductions received:', data);
      setDeductions(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('[EmployeeView] Failed to load deductions:', err);
      alert(err?.message || "Failed to load deductions");
      setDeductions([]);
    } finally { setLoadingDeductions(false); }
  };

  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const userId = resolveNumericUserId();
      console.log('[EmployeeView] Loading salary history for userId:', userId);
      const data = userId ? await getSalaryHistory({ employee: userId }) : await getSalaryHistory();
      console.log('[EmployeeView] Salary history received:', data);
      setHistory(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('[EmployeeView] Failed to load salary history:', err);
      alert(err?.message || "Failed to load salary history");
      setHistory([]);
    } finally { setLoadingHistory(false); }
  };

  const handleDownload = async (p) => {
    try {
      const id = p.id ?? p.pk;
      if (!id) return alert("No payslip id");
      setDownloading(true);
      const { blob, filename } = await downloadPayslip(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err?.message || "Failed to download payslip");
    } finally { setDownloading(false); }
  };

  return (
    <div className="container my-3">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h3 className="mb-0">My Payroll</h3>
          <div className="text-muted small">Summary & documents</div>
        </div>
        <div className="btn-group">
          <button className={`btn btn-sm ${activeTab === "current" ? "btn-primary" : "btn-outline-primary"}`} onClick={() => setActiveTab("current")}>Current</button>
          <button className={`btn btn-sm ${activeTab === "payslips" ? "btn-primary" : "btn-outline-primary"}`} onClick={() => { setActiveTab("payslips"); loadPayslips(); loadDeductions(); }}>Payslips</button>
          <button className={`btn btn-sm ${activeTab === "deductions" ? "btn-primary" : "btn-outline-primary"}`} onClick={() => { setActiveTab("deductions"); loadDeductions(); }}>Deductions</button>
          <button className={`btn btn-sm ${activeTab === "history" ? "btn-primary" : "btn-outline-primary"}`} onClick={() => { setActiveTab("history"); loadHistory(); }}>History</button>
        </div>
      </div>

      {activeTab === "current" && (
        <>
          {loadingPayroll ? (
            <div className="p-3 text-center"><div className="spinner-border" /></div>
          ) : payroll ? (
            <div className="row">
              <div className="col-md-6">
                <div className="card mb-3">
                  <div className="card-body">
                    <h5 className="card-title mb-3">Current Salary</h5>
                    <table className="table table-borderless mb-0">
                      <tbody>
                        <tr><th>Month</th><td>{payroll.month ?? "Current"}</td></tr>
                        <tr><th>Basic</th><td>{currencyINR(extractAmounts(payroll).basic)}</td></tr>
                        <tr><th>Allowances</th><td>{currencyINR(extractAmounts(payroll).allowances)}</td></tr>
                        <tr><th>Deductions</th><td>{currencyINR(extractAmounts(payroll).deductions)}</td></tr>
                        <tr><th>Net</th><td className="fw-semibold">{currencyINR(extractAmounts(payroll).net)}</td></tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
              {payroll.payslip_url && (
                <div className="col-md-6">
                  <div className="card mb-3">
                    <div className="card-body">
                      <h5 className="card-title">Payslip</h5>
                      <p className="mb-2">A payslip is available for download.</p>
                      <a className="btn btn-outline-primary" href={payroll.payslip_url} target="_blank" rel="noreferrer">Download Payslip</a>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="alert alert-warning">No active salary found. Contact HR.</div>
          )}
        </>
      )}

      {activeTab === "payslips" && (
        <>
          <div className="card mb-3">
            <div className="card-body p-0">
              {loadingPayslips ? (
                <div className="p-4 text-center"><div className="spinner-border" /></div>
              ) : payslips.length === 0 ? (
                <div className="p-4 text-center text-muted">No payslips yet.</div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-sm mb-0">
                    <thead className="table-light">
                      <tr><th>ID</th><th>Month</th><th>Status</th><th className="text-end">Actions</th></tr>
                    </thead>
                    <tbody>
                      {payslips.map((p) => {
                        const statusStr = String((p.status ?? "").toUpperCase() || "");
                        const isPaid = !!p.is_paid || statusStr === "PAID";
                        const display = isPaid ? "Paid" : p.status ?? "Generated";
                        return (
                          <tr key={p.id ?? p.pk}>
                            <td>{p.id ?? p.pk}</td>
                            <td>{p.month ?? p.period ?? "—"}</td>
                            <td>{display}</td>
                            <td className="text-end">
                              <button className="btn btn-sm btn-outline-primary" onClick={() => handleDownload(p)} disabled={downloading}>Download</button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          <h5 className="mb-2">My Deductions</h5>
          <div className="card">
            <div className="card-body p-0">
              {loadingDeductions ? (
                <div className="p-3 text-center"><div className="spinner-border" /></div>
              ) : deductions.length === 0 ? (
                <div className="p-3 text-muted text-center">No deductions.</div>
              ) : (
                <div className="table-responsive">
                  <table className="table table-sm mb-0">
                    <thead className="table-light">
                      <tr><th>ID</th><th>Type</th><th>Total</th><th>Installment</th><th>Remaining</th><th>Period</th><th>Status</th></tr>
                    </thead>
                    <tbody>
                      {deductions.map((d) => {
                        const status = Number(d.remaining_amount) <= 0 ? "Completed" : "Active";
                        const period = d.start_month ? `${d.start_month}/${d.start_year ?? ""} - ${d.end_month ?? ""}/${d.end_year ?? ""}` : "—";
                        return (
                          <tr key={d.id ?? d.pk}>
                            <td>{d.id ?? d.pk}</td>
                            <td>{d.deduction_type ?? d.type ?? "—"}</td>
                            <td>{currencyINR(d.total_amount ?? d.amount ?? 0)}</td>
                            <td>{currencyINR(d.installment_amount ?? 0)}</td>
                            <td>{currencyINR(d.remaining_amount ?? 0)}</td>
                            <td>{period}</td>
                            <td><span className={`badge ${status === "Completed" ? "bg-success" : "bg-secondary"}`}>{status}</span></td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {activeTab === "deductions" && (
        <div className="card">
          <div className="card-body p-0">
            {loadingDeductions ? (
              <div className="p-3 text-center"><div className="spinner-border" /></div>
            ) : deductions.length === 0 ? (
              <div className="p-3 text-muted text-center">No deductions.</div>
            ) : (
              <div className="table-responsive">
                <table className="table table-sm mb-0">
                  <thead className="table-light">
                    <tr><th>ID</th><th>Type</th><th>Total</th><th>Installment</th><th>Remaining</th><th>Period</th><th>Status</th></tr>
                  </thead>
                  <tbody>
                    {deductions.map((d) => {
                      const status = Number(d.remaining_amount) <= 0 ? "Completed" : "Active";
                      const period = d.start_month ? `${d.start_month}/${d.start_year ?? ""} - ${d.end_month ?? ""}/${d.end_year ?? ""}` : "—";
                      return (
                        <tr key={d.id ?? d.pk}>
                          <td>{d.id ?? d.pk}</td>
                          <td>{d.deduction_type ?? d.type ?? "—"}</td>
                          <td>{currencyINR(d.total_amount ?? d.amount ?? 0)}</td>
                          <td>{currencyINR(d.installment_amount ?? 0)}</td>
                          <td>{currencyINR(d.remaining_amount ?? 0)}</td>
                          <td>{period}</td>
                          <td><span className={`badge ${status === "Completed" ? "bg-success" : "bg-secondary"}`}>{status}</span></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "history" && (
        <div className="card">
          <div className="card-body p-0">
            {loadingHistory ? (
              <div className="p-3 text-center"><div className="spinner-border" /></div>
            ) : history.length === 0 ? (
              <div className="p-3 text-muted text-center">No history.</div>
            ) : (
              <div className="table-responsive">
                <table className="table table-sm mb-0">
                  <thead className="table-light">
                    <tr><th>Month</th><th>Basic</th><th>Net</th></tr>
                  </thead>
                  <tbody>
                    {history.map((h) => {
                      const a = extractAmounts(h);
                      return (
                        <tr key={h.id ?? `${h.month}-${Math.random()}`}>
                          <td>{h.month ?? "—"}</td>
                          <td>{currencyINR(a.basic)}</td>
                          <td>{currencyINR(a.net)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
