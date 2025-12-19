// src/pages/ExpensesPanel.jsx
import React, { useEffect, useState, useRef, useMemo } from "react";
import { useAuth } from "../context/AuthContext";
import ExpensesAPI from "../api/expenses";

const currencyINR = (v) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR" }).format(Number(v || 0));

const statusLabels = {
  DRAFT: "Draft",
  SUBMITTED: "Submitted",
  UNDER_REVIEW: "Under Review",
  APPROVED: "Approved",
  REJECTED: "Rejected",
  REIMBURSED: "Reimbursed",
};

function normalizeList(resp) {
  if (!resp) return [];
  if (Array.isArray(resp)) return resp;
  if (Array.isArray(resp.results)) return resp.results;
  if (Array.isArray(resp.data)) return resp.data;
  if (Array.isArray(resp.items)) return resp.items;
  return [];
}

function canBeReviewed(status) {
  if (!status) return false;
  const s = String(status).trim().toUpperCase();
  return s === "SUBMITTED" || s === "UNDER_REVIEW" || s === "PENDING" || s === "AWAITING_APPROVAL";
}

function statusBadge(status) {
  const s = (status || "").toUpperCase();
  switch (s) {
    case "DRAFT":
      return <span className="badge bg-secondary">Draft</span>;
    case "SUBMITTED":
      return <span className="badge bg-warning text-dark">Submitted</span>;
    case "UNDER_REVIEW":
      return <span className="badge bg-info text-dark">Under Review</span>;
    case "APPROVED":
      return <span className="badge bg-success">Approved</span>;
    case "REJECTED":
      return <span className="badge bg-danger">Rejected</span>;
    case "REIMBURSED":
      return <span className="badge bg-primary">Reimbursed</span>;
    default:
      return <span className="badge bg-light text-dark">{status || "-"}</span>;
  }
}

export default function ExpensesPanel() {
  const { user } = useAuth();
  const role = ((user && user.role) || "employee").toLowerCase();
  const isAdmin = role === "admin";
  const isHR = role === "hr";
  const isManager = role === "manager";
  const isEmployee = role === "employee";
  const isIntern = role === "intern";

  const userId = user?.id || user?.pk || null;

  const [categories, setCategories] = useState([]);
  const [claims, setClaims] = useState([]);
  const [myClaims, setMyClaims] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [stats, setStats] = useState(null);

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const [categoryTypes, setCategoryTypes] = useState([]);
  const [reimbursementModes, setReimbursementModes] = useState([]);

  // claim modal
  const [showClaimModal, setShowClaimModal] = useState(false);
  const [editingClaim, setEditingClaim] = useState(null);
  const [claimForm, setClaimForm] = useState({
    title: "",
    category: "",
    expense_date: "",
    amount: "",
    notes: "",
  });
  const [claimReceipts, setClaimReceipts] = useState([]);

  // receipt modal
  const [showReceiptModal, setShowReceiptModal] = useState(false);
  const [receiptFile, setReceiptFile] = useState(null);
  const [receiptMeta, setReceiptMeta] = useState({
    amount: "",
    receipt_date: "",
    vendor_name: "",
    receipt_number: "",
  });

  // review modal
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewClaim, setReviewClaim] = useState(null);
  const [reviewForm, setReviewForm] = useState({ action: "APPROVE", reviewNotes: "", adjustedAmount: "" });

  // reimburse modal
  const [showReimburseModal, setShowReimburseModal] = useState(false);
  const [reimburseClaim, setReimburseClaim] = useState(null);
  const [reimburseForm, setReimburseForm] = useState({ reimbursement_mode: "", reimbursement_reference: "", notes: "" });

  // category modal
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [categoryForm, setCategoryForm] = useState({
    name: "",
    max_amount: "",
    requires_receipt: false,
    approval_required: true,
    is_active: true,
    category_type: "",
  });

  // history modal
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [historyEntries, setHistoryEntries] = useState([]);

  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    loadInitial();
    loadBackendChoices();
    return () => {
      mountedRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadInitial() {
    setLoading(true);
    setErrorMsg(null);
    try {
      await Promise.all([loadCategories(), loadRoleListsAndStats()]);
    } catch (err) {
      console.error("loadInitial", err);
      setErrorMsg(String(err?.message || err));
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }

  // load OPTIONS to pick valid enums (if backend supports it)
  async function loadBackendChoices() {
    try {
      const BASE = (process.env.REACT_APP_API_BASE || "http://localhost:8000").replace(/\/$/, "");
      const token =
        localStorage.getItem("access_token") || localStorage.getItem("access") || localStorage.getItem("token") || null;
      const headers = { Accept: "application/json" };
      if (token) headers.Authorization = `Bearer ${token}`;

      try {
        const resp = await fetch(`${BASE}/api/expenses/categories/`, { method: "OPTIONS", headers });
        if (resp.ok) {
          const data = await resp.json().catch(() => null);
          const choices = data?.actions?.POST?.category_type?.choices || data?.schema?.properties?.category_type?.enum;
          if (Array.isArray(choices) && choices.length) {
            const vals = choices.map((c) => (typeof c === "string" ? c : c.value ?? c[0] ?? ""));
            setCategoryTypes(vals.filter(Boolean));
          }
        }
      } catch (e) {
        // ignore
      }

      try {
        const resp2 = await fetch(`${BASE}/api/expenses/claims/`, { method: "OPTIONS", headers });
        if (resp2.ok) {
          const d2 = await resp2.json().catch(() => null);
          const enumVals = d2?.schema?.properties?.reimbursement_mode?.enum || d2?.actions?.POST?.reimbursement_mode?.choices;
          if (Array.isArray(enumVals) && enumVals.length) {
            const vals = enumVals.map((c) => (typeof c === "string" ? c : c.value ?? c[0] ?? ""));
            setReimbursementModes(vals.filter(Boolean));
          }
        }
      } catch (e) {
        // ignore
      }
    } catch (err) {
      console.warn("loadBackendChoices", err);
    }
  }

  async function loadCategories() {
    try {
      const data = await ExpensesAPI.fetchExpenseCategories();
      setCategories(normalizeList(data));
    } catch (err) {
      console.error("loadCategories", err);
      setCategories([]);
    }
  }

  async function loadRoleListsAndStats() {
    try {
      let all = [];
      try {
        const allResp = await ExpensesAPI.fetchClaims();
        all = normalizeList(allResp);
        setClaims(all);
      } catch (e) {
        console.warn("fetchClaims failed:", e);
        setClaims([]);
        all = [];
      }

      if (isEmployee || isIntern) {
        try {
          const myResp = await ExpensesAPI.fetchMyClaims();
          setMyClaims(normalizeList(myResp));
        } catch (e) {
          console.warn("fetchMyClaims failed, falling back:", e);
          const mine = all.filter((c) => String(c.employee || c.employee_id || c.created_by || c.user) === String(userId));
          setMyClaims(mine);
        }
      } else {
        setMyClaims([]);
      }

      if (isManager || isHR || isAdmin) {
        try {
          const pResp = await ExpensesAPI.fetchPendingApprovals();
          const parr = normalizeList(pResp);
          if (parr && parr.length) setPendingApprovals(parr);
          else {
            const pending = all.filter((c) => canBeReviewed(c.status));
            setPendingApprovals(pending);
          }
        } catch (e) {
          console.warn("fetchPendingApprovals failed, falling back:", e);
          const pending = all.filter((c) => canBeReviewed(c.status));
          setPendingApprovals(pending);
        }
      } else {
        setPendingApprovals([]);
      }

      if (isAdmin || isHR) {
        try {
          const s = await ExpensesAPI.fetchExpenseStatistics();
          if (s && (s.submitted_count != null || s.totals != null)) {
            setStats(s);
          } else {
            setStats(null);
          }
        } catch (e) {
          console.warn("fetchExpenseStatistics failed, fallback will compute:", e);
          setStats(null);
        }
      } else {
        setStats(null);
      }
    } catch (err) {
      console.error("loadRoleListsAndStats", err);
    }
  }

  const derivedStats = useMemo(() => {
    const map = new Map();
    (Array.isArray(claims) ? claims : []).forEach((c) => {
      if (c && c.id != null) map.set(String(c.id), c);
    });
    (Array.isArray(myClaims) ? myClaims : []).forEach((c) => {
      if (c && c.id != null) map.set(String(c.id), c);
    });
    (Array.isArray(pendingApprovals) ? pendingApprovals : []).forEach((c) => {
      if (c && c.id != null) map.set(String(c.id), c);
    });
    const combined = Array.from(map.values());
    const submitted_count = combined.filter((c) => ((c.status || "").toUpperCase() === "SUBMITTED")).length;
    const approved_count = combined.filter((c) => ((c.status || "").toUpperCase() === "APPROVED")).length;
    const rejected_count = combined.filter((c) => ((c.status || "").toUpperCase() === "REJECTED")).length;
    const reimbursed_count = combined.filter((c) => ((c.status || "").toUpperCase() === "REIMBURSED")).length;
    const totals = combined.reduce((s, c) => s + (Number(c.amount) || 0), 0);
    return { submitted_count, approved_count, rejected_count, reimbursed_count, totals };
  }, [claims, myClaims, pendingApprovals]);

  const statsToShow = stats || derivedStats;

  // ---------- Claim create/edit ----------
  function openClaimCreate() {
    if (!isEmployee) {
      alert("Only employees can create claims.");
      return;
    }
    setEditingClaim(null);
    setClaimForm({ title: "", category: "", expense_date: "", amount: "", notes: "" });
    setClaimReceipts([]);
    setShowClaimModal(true);
  }

  async function openClaimEdit(c) {
    const owner = String(c.employee || c.employee_id || c.created_by || c.user) === String(userId);
    if (!(owner || isAdmin || isHR)) {
      alert("Only owners (draft) or admin/hr can edit this claim.");
      return;
    }
    setEditingClaim(c);
    setClaimForm({
      title: c.title || "",
      category: c.category || c.category_id || "",
      expense_date: c.expense_date || "",
      amount: c.amount || "",
      notes: c.notes || "",
    });
    try {
      const r = await ExpensesAPI.fetchReceipts({ claim: c.id });
      setClaimReceipts(normalizeList(r));
    } catch (e) {
      setClaimReceipts([]);
    }
    setShowClaimModal(true);
  }

  function handleClaimChange(e) {
    const { name, value, type, checked } = e.target;
    setClaimForm((p) => ({ ...p, [name]: type === "checkbox" ? checked : value }));
  }

  function validateClaimForm() {
    const { title, category, expense_date, amount } = claimForm;
    if (!title || !category || !expense_date || !amount) return { ok: false, reason: "Please fill required fields" };
    const ed = new Date(expense_date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (ed > today) return { ok: false, reason: "Expense date cannot be in the future" };
    return { ok: true };
  }

  async function saveClaim(e) {
    e.preventDefault();
    setErrorMsg(null);
    const v = validateClaimForm();
    if (!v.ok) {
      alert(v.reason);
      return;
    }
    setLoading(true);
    try {
      const payload = {
        title: claimForm.title,
        category: claimForm.category,
        expense_date: claimForm.expense_date,
        amount: Number(claimForm.amount),
        notes: claimForm.notes || "",
        description: claimForm.notes || "", // include description in case backend expects it
      };
      if (editingClaim && editingClaim.id) {
        await ExpensesAPI.updateClaim(editingClaim.id, payload);
      } else {
        await ExpensesAPI.createClaim(payload);
      }
      await loadRoleListsAndStats();
      setShowClaimModal(false);
    } catch (err) {
      console.error("saveClaim", err);
      if (err?.body) {
        const b = err.body;
        if (typeof b === "object") {
          const messages = Object.keys(b)
            .map((k) => `${k}: ${Array.isArray(b[k]) ? b[k].join(", ") : b[k]}`)
            .join(" | ");
          alert(messages);
        } else {
          alert(String(err.message || err));
        }
      } else {
        alert(String(err.message || err));
      }
    } finally {
      setLoading(false);
    }
  }

  // ---------- Submit ----------
  async function submitClaim(claimId) {
    if (!window.confirm("Submit claim for approval?")) return;
    setLoading(true);
    try {
      let receipts = claimReceipts || [];
      if (!receipts || receipts.length === 0) {
        try {
          const r = await ExpensesAPI.fetchReceipts({ claim: claimId });
          receipts = normalizeList(r);
        } catch (e) {
          receipts = [];
        }
      }
      const claimObj =
        claims.find((c) => String(c.id) === String(claimId)) ||
        myClaims.find((c) => String(c.id) === String(claimId)) ||
        editingClaim ||
        null;
      const catId = claimObj?.category || claimForm.category || null;
      const cat = categories.find((cc) => String(cc.id) === String(catId));
      if (cat && cat.requires_receipt) {
        if (!receipts || receipts.length === 0) {
          alert("This category requires at least one receipt. Please upload a receipt before submitting.");
          const claimToOpen = claimObj || { id: claimId, title: "" };
          setEditingClaim(claimToOpen);
          setShowReceiptModal(true);
          setLoading(false);
          return;
        }
      }
      await ExpensesAPI.submitClaim(claimId, "");
      await loadRoleListsAndStats();
      alert("Claim submitted");
    } catch (err) {
      console.error("submitClaim", err);
      if (err?.body) {
        const b = err.body;
        if (typeof b === "object") {
          const messages = Object.keys(b)
            .map((k) => `${k}: ${Array.isArray(b[k]) ? b[k].join(", ") : b[k]}`)
            .join(" | ");
          alert(messages);
        } else {
          alert(String(err.message || err));
        }
      } else {
        alert(String(err.message || err));
      }
    } finally {
      setLoading(false);
    }
  }

  // ---------- Receipts ----------
  function openReceiptModal(claim = null) {
    setEditingClaim(claim);
    setReceiptFile(null);
    setReceiptMeta({ amount: "", receipt_date: "", vendor_name: "", receipt_number: "" });
    setShowReceiptModal(true);
  }

  function handleReceiptFile(e) {
    const f = e.target.files[0] || null;
    setReceiptFile(f);
  }

  async function uploadReceipt(e) {
    e.preventDefault();
    if (!receiptFile) {
      alert("Pick a file");
      return;
    }
    setLoading(true);
    try {
      await ExpensesAPI.uploadReceipt({
        claimId: editingClaim?.id || null,
        file: receiptFile,
        amount: receiptMeta.amount || null,
        receiptDate: receiptMeta.receipt_date || null,
        vendorName: receiptMeta.vendor_name || null,
        receiptNumber: receiptMeta.receipt_number || null,
      });
      alert("Uploaded");
      setShowReceiptModal(false);
      await loadRoleListsAndStats();
    } catch (err) {
      console.error("uploadReceipt", err);
      if (err?.body) {
        const b = err.body;
        if (typeof b === "object") {
          const messages = Object.keys(b)
            .map((k) => `${k}: ${Array.isArray(b[k]) ? b[k].join(", ") : b[k]}`)
            .join(" | ");
          alert(messages);
        } else {
          alert(String(err.message || err));
        }
      } else {
        alert(String(err.message || err));
      }
    } finally {
      setLoading(false);
    }
  }

  // ---------- Review ----------
  function openReviewModal(c) {
    if (!(isAdmin || isHR || isManager)) {
      alert("Not authorized");
      return;
    }
    setReviewClaim(c);
    setReviewForm({ action: "APPROVE", reviewNotes: "", adjustedAmount: c?.amount || "" });
    setShowReviewModal(true);
  }

  async function doReview(e) {
    e.preventDefault();
    if (!reviewClaim) return;
    if (!canBeReviewed(reviewClaim.status)) {
      alert("Only SUBMITTED or UNDER_REVIEW claims can be approved/rejected.");
      return;
    }
    setLoading(true);
    try {
      await ExpensesAPI.reviewClaim(reviewClaim.id, {
        action: reviewForm.action === "APPROVE" ? "APPROVE" : "REJECT",
        reviewNotes: reviewForm.reviewNotes,
        adjustedAmount: reviewForm.adjustedAmount ? Number(reviewForm.adjustedAmount) : null,
      });
      alert("Review submitted");
      setShowReviewModal(false);
      await loadRoleListsAndStats();
    } catch (err) {
      console.error("doReview", err);
      if (err?.body) {
        const b = err.body;
        if (typeof b === "object") {
          const messages = Object.keys(b)
            .map((k) => `${k}: ${Array.isArray(b[k]) ? b[k].join(", ") : b[k]}`)
            .join(" | ");
          alert(messages);
        } else {
          alert(String(err.message || err));
        }
      } else {
        alert(String(err.message || err));
      }
    } finally {
      setLoading(false);
    }
  }

  async function quickApprove(claimId, claimStatus) {
    if (!(isAdmin || isHR || isManager)) {
      alert("Not authorized");
      return;
    }
    if (!canBeReviewed(claimStatus)) {
      alert("Only SUBMITTED or UNDER_REVIEW claims can be approved.");
      return;
    }
    if (!window.confirm("Approve this claim?")) return;
    setLoading(true);
    try {
      await ExpensesAPI.reviewClaim(claimId, { action: "APPROVE", reviewNotes: "" });
      alert("Claim approved");
      await loadRoleListsAndStats();
    } catch (err) {
      console.error("quickApprove", err);
      if (err?.body) {
        const b = err.body;
        if (typeof b === "object") {
          const messages = Object.keys(b)
            .map((k) => `${k}: ${Array.isArray(b[k]) ? b[k].join(", ") : b[k]}`)
            .join(" | ");
          alert(messages);
        } else {
          alert(String(err.message || err));
        }
      } else {
        alert(String(err.message || err));
      }
    } finally {
      setLoading(false);
    }
  }

  async function quickReject(claimId, claimStatus) {
    if (!(isAdmin || isHR || isManager)) {
      alert("Not authorized");
      return;
    }
    if (!canBeReviewed(claimStatus)) {
      alert("Only SUBMITTED or UNDER_REVIEW claims can be rejected.");
      return;
    }
    const reason = window.prompt("Reason for rejection (optional):", "");
    if (reason === null) return;
    setLoading(true);
    try {
      await ExpensesAPI.reviewClaim(claimId, { action: "REJECT", reviewNotes: reason || "" });
      alert("Claim rejected");
      await loadRoleListsAndStats();
    } catch (err) {
      console.error("quickReject", err);
      if (err?.body) {
        const b = err.body;
        if (typeof b === "object") {
          const messages = Object.keys(b)
            .map((k) => `${k}: ${Array.isArray(b[k]) ? b[k].join(", ") : b[k]}`)
            .join(" | ");
          alert(messages);
        } else {
          alert(String(err.message || err));
        }
      } else {
        alert(String(err.message || err));
      }
    } finally {
      setLoading(false);
    }
  }

  // ---------- Reimburse ----------
  function openReimburseModal(claim) {
    if (!(isAdmin || isHR)) {
      alert("Only Admin/HR can mark reimbursements.");
      return;
    }
    setReimburseClaim(claim);
    setReimburseForm({ reimbursement_mode: "", reimbursement_reference: "", notes: "" });
    setShowReimburseModal(true);
  }

  async function submitReimburse(e) {
    e.preventDefault();
    if (!reimburseClaim) return;
    if (!reimburseForm.reimbursement_mode || !reimburseForm.reimbursement_reference) {
      alert("Please fill reimbursement mode and reference.");
      return;
    }
    setLoading(true);
    try {
      await ExpensesAPI.reimburseClaim(reimburseClaim.id, {
        reimbursement_mode: reimburseForm.reimbursement_mode,
        reimbursement_reference: reimburseForm.reimbursement_reference,
        notes: reimburseForm.notes || "",
      });
      alert("Marked reimbursed");
      setShowReimburseModal(false);
      await loadRoleListsAndStats();
    } catch (err) {
      console.error("submitReimburse", err);
      if (err?.body) {
        const b = err.body;
        if (typeof b === "object") {
          const messages = Object.keys(b)
            .map((k) => `${k}: ${Array.isArray(b[k]) ? b[k].join(", ") : b[k]}`)
            .join(" | ");
          alert(messages);
        } else {
          alert(String(err.message || err));
        }
      } else {
        alert(String(err.message || err));
      }
    } finally {
      setLoading(false);
    }
  }

  // ---------- Categories ----------
  function openCategoryCreate() {
    if (!(isAdmin || isHR)) {
      alert("Not authorized");
      return;
    }
    setEditingCategory(null);
    setCategoryForm({ name: "", max_amount: "", requires_receipt: false, approval_required: true, is_active: true, category_type: "" });
    setShowCategoryModal(true);
  }

  function openCategoryEdit(cat) {
    if (!(isAdmin || isHR)) {
      alert("Not authorized");
      return;
    }
    setEditingCategory(cat);
    setCategoryForm({
      name: cat.name || "",
      max_amount: cat.max_amount || "",
      requires_receipt: !!cat.requires_receipt,
      approval_required: !!cat.approval_required,
      is_active: cat.is_active != null ? !!cat.is_active : true,
      category_type: cat.category_type || cat.type || "",
    });
    setShowCategoryModal(true);
  }

  async function saveCategory(e) {
    e.preventDefault();
    if (!(isAdmin || isHR)) {
      alert("Not authorized");
      return;
    }
    setLoading(true);
    try {
      const payload = {
        name: categoryForm.name,
        max_amount: Number(categoryForm.max_amount) || 0,
        requires_receipt: Boolean(categoryForm.requires_receipt),
        approval_required: Boolean(categoryForm.approval_required),
        is_active: Boolean(categoryForm.is_active),
        category_type: categoryForm.category_type || undefined,
      };
      if (editingCategory && editingCategory.id) {
        await ExpensesAPI.patchExpenseCategory(editingCategory.id, payload);
      } else {
        await ExpensesAPI.createExpenseCategory(payload);
      }
      await loadCategories();
      setShowCategoryModal(false);
    } catch (err) {
      console.error("saveCategory", err);
      if (err?.body) {
        const b = err.body;
        if (typeof b === "object") {
          const messages = Object.keys(b)
            .map((k) => `${k}: ${Array.isArray(b[k]) ? b[k].join(", ") : b[k]}`)
            .join(" | ");
          alert(messages);
        } else {
          alert(String(err.message || err));
        }
      } else {
        alert(String(err.message || err));
      }
    } finally {
      setLoading(false);
    }
  }

  async function removeCategory(id) {
    if (!isAdmin) {
      alert("Only admin can delete categories.");
      return;
    }
    if (!window.confirm("Delete category?")) return;
    try {
      await ExpensesAPI.deleteExpenseCategory(id);
      await loadCategories();
    } catch (err) {
      console.error("removeCategory", err);
      alert("Delete failed");
    }
  }

  // ---------- History ----------
  async function openHistory(claimId) {
    setShowHistoryModal(true);
    try {
      const h = await ExpensesAPI.fetchClaimHistory({ claim: claimId });
      setHistoryEntries(normalizeList(h));
    } catch (err) {
      console.error("openHistory", err);
      setHistoryEntries([]);
    }
  }

  // permission guard
  if (!["employee", "hr", "admin", "manager", "intern"].includes(role)) {
    return (
      <div className="container py-4">
        <div className="alert alert-warning">You don't have access to Expenses. Contact admin.</div>
      </div>
    );
  }

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h3 className="mb-0">Expenses & Reimbursements</h3>
          <div className="small text-muted">Claims, receipts, reviews and reimbursements</div>
        </div>

        <div className="d-flex gap-2">
          {(isAdmin || isHR) && (
            <button className="btn btn-outline-primary" onClick={openCategoryCreate} disabled={loading}>
              Manage Categories
            </button>
          )}
          {isEmployee && (
            <button className="btn btn-primary" onClick={openClaimCreate} disabled={loading}>
              + New Claim
            </button>
          )}
        </div>
      </div>

      {errorMsg && <div className="alert alert-danger">{errorMsg}</div>}
      {loading && <div className="alert alert-info">Loading...</div>}

      {statsToShow && (
        <div className="card mb-3">
          <div className="card-body d-flex gap-3 align-items-center">
            <div className="text-center">
              <div className="small text-muted">Submitted</div>
              <div className="h4">{statsToShow.submitted_count ?? "-"}</div>
            </div>
            <div className="text-center">
              <div className="small text-muted">Approved</div>
              <div className="h4">{statsToShow.approved_count ?? "-"}</div>
            </div>
            <div className="text-center">
              <div className="small text-muted">Rejected</div>
              <div className="h4">{statsToShow.rejected_count ?? "-"}</div>
            </div>
            <div className="text-center">
              <div className="small text-muted">Reimbursed</div>
              <div className="h4">{statsToShow.reimbursed_count ?? "-"}</div>
            </div>
            <div className="ms-auto small text-muted">{statsToShow.totals ? `Total: ${currencyINR(statsToShow.totals)}` : ""}</div>
          </div>
        </div>
      )}

      <div className="row">
        <div className="col-md-6">
          {/* My Claims */}
          <div className="card mb-3 shadow-sm">
            <div className="card-header d-flex justify-content-between align-items-center">
              <strong>My Claims</strong>
              <small className="text-muted">{myClaims.length}</small>
            </div>
            <div className="card-body p-0">
              <div className="table-responsive">
                <table className="table table-hover table-sm mb-0">
                  <thead className="table-light">
                    <tr>
                      <th>Title</th>
                      <th>Category</th>
                      <th>Amount</th>
                      <th>Date</th>
                      <th>Status</th>
                      <th className="text-end">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {myClaims.length === 0 && (
                      <tr>
                        <td colSpan="6" className="text-center py-3">No claims</td>
                      </tr>
                    )}
                    {myClaims.map((c) => (
                      <tr key={c.id}>
                        <td style={{ maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.title}</td>
                        <td>{c.category_name || c.category || "-"}</td>
                        <td>{currencyINR(c.amount)}</td>
                        <td>{c.expense_date || "-"}</td>
                        <td>{statusBadge(c.status)}</td>
                        <td className="text-end">
                          <div className="btn-group btn-group-sm" role="group">
                            <button className="btn btn-outline-primary" onClick={() => openClaimEdit(c)} disabled={loading}>Edit</button>
                            {String((c.status || "").toUpperCase()) === "DRAFT" && (
                              <button className="btn btn-success" onClick={() => submitClaim(c.id)} disabled={loading}>Submit</button>
                            )}
                            <button className="btn btn-outline-secondary" onClick={() => openReceiptModal(c)} disabled={loading}>Receipts</button>
                            <button className="btn btn-outline-info" onClick={() => openHistory(c.id)} disabled={loading}>History</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Pending Approvals */}
          {(isManager || isHR || isAdmin) && (
            <div className="card mb-3 shadow-sm">
              <div className="card-header d-flex justify-content-between align-items-center">
                <strong>Pending Approvals</strong>
                <small className="text-muted">{pendingApprovals.length}</small>
              </div>
              <div className="card-body p-0">
                <div className="table-responsive">
                  <table className="table table-hover table-sm mb-0">
                    <thead className="table-light">
                      <tr>
                        <th>Title</th>
                        <th>Employee</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th className="text-end">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pendingApprovals.length === 0 && (
                        <tr>
                          <td colSpan="5" className="text-center py-3">No pending approvals</td>
                        </tr>
                      )}
                      {pendingApprovals.map((p) => (
                        <tr key={p.id}>
                          <td style={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.title}</td>
                          <td>{p.employee_name || p.employee_email || p.employee || p.created_by || "-"}</td>
                          <td>{currencyINR(p.amount)}</td>
                          <td>{statusBadge(p.status)}</td>
                          <td className="text-end">
                            <div className="btn-group btn-group-sm" role="group">
                              {canBeReviewed(p.status) && <button className="btn btn-primary" onClick={() => openReviewModal(p)} disabled={loading}>Review</button>}
                              {canBeReviewed(p.status) && <button className="btn btn-success" onClick={() => quickApprove(p.id, p.status)} disabled={loading}>Approve</button>}
                              {canBeReviewed(p.status) && <button className="btn btn-danger" onClick={() => quickReject(p.id, p.status)} disabled={loading}>Reject</button>}
                              <button className="btn btn-outline-info" onClick={() => openHistory(p.id)} disabled={loading}>History</button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="col-md-6">
          {/* All claims */}
          {(isAdmin || isHR) && (
            <div className="card mb-3 shadow-sm">
              <div className="card-header"><strong>All Claims</strong></div>
              <div className="card-body p-0">
                <div className="table-responsive">
                  <table className="table table-hover table-sm mb-0">
                    <thead className="table-light">
                      <tr>
                        <th>Title</th>
                        <th>By</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th className="text-end">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {claims.length === 0 && (
                        <tr>
                          <td colSpan="5" className="text-center py-3">No claims</td>
                        </tr>
                      )}
                      {claims.map((c) => (
                        <tr key={c.id}>
                          <td style={{ maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.title}</td>
                          <td>{c.employee_name || c.employee_email || c.employee || c.created_by || "-"}</td>
                          <td>{currencyINR(c.amount)}</td>
                          <td>{statusBadge(c.status)}</td>
                          <td className="text-end">
                            <div className="btn-group btn-group-sm" role="group">
                              <button className="btn btn-outline-secondary" onClick={() => openReceiptModal(c)} disabled={loading}>Receipts</button>
                              {c.status === "APPROVED" && (isAdmin || isHR) && <button className="btn btn-success" onClick={() => openReimburseModal(c)} disabled={loading}>Mark Reimbursed</button>}
                              {(isManager || isHR || isAdmin) && <button className="btn btn-outline-primary" onClick={() => openReviewModal(c)} disabled={loading}>Review</button>}
                              {(isManager || isHR || isAdmin) && canBeReviewed(c.status) && <button className="btn btn-success" onClick={() => quickApprove(c.id, c.status)} disabled={loading}>Approve</button>}
                              {(isManager || isHR || isAdmin) && canBeReviewed(c.status) && <button className="btn btn-danger" onClick={() => quickReject(c.id, c.status)} disabled={loading}>Reject</button>}
                              <button className="btn btn-outline-info" onClick={() => openHistory(c.id)} disabled={loading}>History</button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Categories */}
          <div className="card mb-3 shadow-sm">
            <div className="card-header d-flex justify-content-between align-items-center">
              <strong>Categories</strong>
              <small className="text-muted">{categories.length}</small>
            </div>
            <div className="card-body">
              {categories.length === 0 && <div className="text-muted">No categories.</div>}
              {categories.map((cat) => (
                <div key={cat.id} className="d-flex justify-content-between align-items-center mb-2">
                  <div>
                    <div className="fw-semibold">{cat.name} {cat.is_active === false && <span className="badge bg-secondary ms-2">Inactive</span>}</div>
                    <div className="small text-muted">
                      Max: {currencyINR(cat.max_amount)} • Type: {cat.category_type || cat.type || "-"} • Receipts: {cat.requires_receipt ? "Yes" : "No"} • Approval: {cat.approval_required ? "Yes" : "No"}
                    </div>
                  </div>
                  {(isAdmin || isHR) ? (
                    <div className="d-flex gap-1">
                      <button className="btn btn-sm btn-outline-warning" onClick={() => openCategoryEdit(cat)} disabled={loading}>Edit</button>
                      {isAdmin && <button className="btn btn-sm btn-outline-danger" onClick={() => removeCategory(cat.id)} disabled={loading}>Delete</button>}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ---------- CLAIM MODAL ---------- */}
      <div
        className={`modal fade ${showClaimModal ? "d-block" : ""}`}
        tabIndex={-1}
        role="dialog"
        style={{ background: showClaimModal ? "rgba(0,0,0,0.45)" : undefined }}
        onClick={() => setShowClaimModal(false)}
      >
        <div className="modal-dialog modal-lg" onClick={(e) => e.stopPropagation()}>
          <form className="modal-content" onSubmit={saveClaim}>
            <div className="modal-header">
              <h5 className="modal-title">{editingClaim ? "Edit Claim" : "New Claim"}</h5>
              <button type="button" className="btn-close" onClick={() => setShowClaimModal(false)} />
            </div>
            <div className="modal-body">
              <div className="row g-2">
                <div className="col-md-6">
                  <label className="form-label">Title</label>
                  <input name="title" className="form-control" value={claimForm.title} onChange={handleClaimChange} required />
                </div>
                <div className="col-md-6">
                  <label className="form-label">Category</label>
                  <select name="category" className="form-select" value={claimForm.category} onChange={handleClaimChange} required>
                    <option value="">-- choose category --</option>
                    {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                  </select>
                </div>
                <div className="col-md-4">
                  <label className="form-label">Expense date</label>
                  <input type="date" name="expense_date" className="form-control" value={claimForm.expense_date} onChange={handleClaimChange} required />
                </div>
                <div className="col-md-4">
                  <label className="form-label">Amount</label>
                  <input type="number" step="0.01" name="amount" className="form-control" value={claimForm.amount} onChange={handleClaimChange} required />
                </div>
                <div className="col-md-4">
                  <label className="form-label">Notes</label>
                  <input name="notes" className="form-control" value={claimForm.notes} onChange={handleClaimChange} />
                </div>
              </div>

              <hr />
              <div>
                <h6>Receipts</h6>
                {claimReceipts.length === 0 && <div className="text-muted">No receipts.</div>}
                {claimReceipts.map((r) => (
                  <div key={r.id} className="d-flex justify-content-between align-items-center mb-2">
                    <div>
                      <div className="fw-semibold">{r.receipt_number || r.vendor_name || "Receipt"}</div>
                      <div className="small text-muted">{r.receipt_date || "-"} • {currencyINR(r.amount)}</div>
                    </div>
                    <div>
                      <a className="btn btn-sm btn-outline-primary me-2" href={r.file} target="_blank" rel="noreferrer">View</a>
                    </div>
                  </div>
                ))}
                <div className="mt-2">
                  <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => openReceiptModal(editingClaim)} disabled={loading}>Upload Receipt</button>
                </div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" type="button" onClick={() => setShowClaimModal(false)}>Close</button>
              <button className="btn btn-primary" type="submit" disabled={loading}>{editingClaim ? "Update" : "Save"}</button>
            </div>
          </form>
        </div>
      </div>

      {/* ---------- RECEIPT MODAL ---------- */}
      <div
        className={`modal fade ${showReceiptModal ? "d-block" : ""}`}
        tabIndex={-1}
        role="dialog"
        style={{ background: showReceiptModal ? "rgba(0,0,0,0.45)" : undefined }}
        onClick={() => setShowReceiptModal(false)}
      >
        <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
          <form className="modal-content" onSubmit={uploadReceipt}>
            <div className="modal-header">
              <h5 className="modal-title">Upload Receipt {editingClaim ? `for ${editingClaim.title}` : ""}</h5>
              <button type="button" className="btn-close" onClick={() => setShowReceiptModal(false)} />
            </div>
            <div className="modal-body">
              <div className="mb-2">
                <label className="form-label">File (PDF / JPG / PNG)</label>
                <input type="file" className="form-control" onChange={handleReceiptFile} required />
              </div>
              <div className="mb-2">
                <label className="form-label">Amount (optional)</label>
                <input type="number" step="0.01" className="form-control" value={receiptMeta.amount} onChange={(e) => setReceiptMeta((p) => ({ ...p, amount: e.target.value }))} />
              </div>
              <div className="mb-2">
                <label className="form-label">Receipt Date (optional)</label>
                <input type="date" className="form-control" value={receiptMeta.receipt_date} onChange={(e) => setReceiptMeta((p) => ({ ...p, receipt_date: e.target.value }))} />
              </div>
              <div className="mb-2">
                <label className="form-label">Vendor Name</label>
                <input className="form-control" value={receiptMeta.vendor_name} onChange={(e) => setReceiptMeta((p) => ({ ...p, vendor_name: e.target.value }))} />
              </div>
              <div className="mb-2">
                <label className="form-label">Receipt Number</label>
                <input className="form-control" value={receiptMeta.receipt_number} onChange={(e) => setReceiptMeta((p) => ({ ...p, receipt_number: e.target.value }))} />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" type="button" onClick={() => setShowReceiptModal(false)}>Close</button>
              <button className="btn btn-primary" type="submit" disabled={loading}>Upload</button>
            </div>
          </form>
        </div>
      </div>

      {/* ---------- REVIEW MODAL ---------- */}
      <div
        className={`modal fade ${showReviewModal ? "d-block" : ""}`}
        tabIndex={-1}
        role="dialog"
        style={{ background: showReviewModal ? "rgba(0,0,0,0.45)" : undefined }}
        onClick={() => setShowReviewModal(false)}
      >
        <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
          <form className="modal-content" onSubmit={doReview}>
            <div className="modal-header">
              <h5 className="modal-title">Review Claim</h5>
              <button type="button" className="btn-close" onClick={() => setShowReviewModal(false)} />
            </div>
            <div className="modal-body">
              <p><strong>Title:</strong> {reviewClaim?.title}</p>
              <p><strong>Employee:</strong> {reviewClaim?.employee_name || reviewClaim?.employee || "-"}</p>
              <p><strong>Amount:</strong> {currencyINR(reviewClaim?.amount)}</p>

              <div className="mb-2">
                <label className="form-label">Action</label>
                <select className="form-select" value={reviewForm.action} onChange={(e) => setReviewForm((p) => ({ ...p, action: e.target.value }))}>
                  <option value="APPROVE">Approve</option>
                  <option value="REJECT">Reject</option>
                </select>
              </div>

              <div className="mb-2">
                <label className="form-label">Adjusted Amount (optional)</label>
                <input type="number" step="0.01" className="form-control" value={reviewForm.adjustedAmount} onChange={(e) => setReviewForm((p) => ({ ...p, adjustedAmount: e.target.value }))} />
              </div>

              <div className="mb-2">
                <label className="form-label">Notes</label>
                <textarea className="form-control" value={reviewForm.reviewNotes} onChange={(e) => setReviewForm((p) => ({ ...p, reviewNotes: e.target.value }))} />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" type="button" onClick={() => setShowReviewModal(false)}>Close</button>
              <button className="btn btn-primary" type="submit" disabled={loading}>Send Review</button>
            </div>
          </form>
        </div>
      </div>

      {/* ---------- REIMBURSE MODAL ---------- */}
      <div
        className={`modal fade ${showReimburseModal ? "d-block" : ""}`}
        tabIndex={-1}
        role="dialog"
        style={{ background: showReimburseModal ? "rgba(0,0,0,0.45)" : undefined }}
        onClick={() => setShowReimburseModal(false)}
      >
        <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
          <form className="modal-content" onSubmit={submitReimburse}>
            <div className="modal-header">
              <h5 className="modal-title">Mark Reimbursed — {reimburseClaim?.title}</h5>
              <button type="button" className="btn-close" onClick={() => setShowReimburseModal(false)} />
            </div>
            <div className="modal-body">
              <div className="mb-2">
                <label className="form-label">Reimbursement Mode</label>
                <select className="form-select" value={reimburseForm.reimbursement_mode} onChange={(e) => setReimburseForm((p) => ({ ...p, reimbursement_mode: e.target.value }))} required>
                  <option value="">-- choose mode --</option>
                  {(reimbursementModes.length ? reimbursementModes : ["BANK_TRANSFER", "NEFT", "IMPS", "CHEQUE"]).map((m) => <option key={m} value={m}>{m}</option>)}
                </select>
              </div>
              <div className="mb-2">
                <label className="form-label">Reference (txn id / cheque no)</label>
                <input className="form-control" value={reimburseForm.reimbursement_reference} onChange={(e) => setReimburseForm((p) => ({ ...p, reimbursement_reference: e.target.value }))} required />
              </div>
              <div className="mb-2">
                <label className="form-label">Notes (optional)</label>
                <textarea className="form-control" value={reimburseForm.notes} onChange={(e) => setReimburseForm((p) => ({ ...p, notes: e.target.value }))} />
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" type="button" onClick={() => setShowReimburseModal(false)}>Close</button>
              <button className="btn btn-primary" type="submit" disabled={loading}>Mark Reimbursed</button>
            </div>
          </form>
        </div>
      </div>

      {/* ---------- CATEGORY MODAL ---------- */}
      <div
        className={`modal fade ${showCategoryModal ? "d-block" : ""}`}
        tabIndex={-1}
        role="dialog"
        style={{ background: showCategoryModal ? "rgba(0,0,0,0.45)" : undefined }}
        onClick={() => setShowCategoryModal(false)}
      >
        <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
          <form className="modal-content" onSubmit={saveCategory}>
            <div className="modal-header">
              <h5 className="modal-title">{editingCategory ? "Edit Category" : "Create Category"}</h5>
              <button type="button" className="btn-close" onClick={() => setShowCategoryModal(false)} />
            </div>
            <div className="modal-body">
              <div className="mb-2">
                <label className="form-label">Name</label>
                <input className="form-control" value={categoryForm.name} onChange={(e) => setCategoryForm((p) => ({ ...p, name: e.target.value }))} required />
              </div>
              <div className="mb-2">
                <label className="form-label">Max amount</label>
                <input type="number" step="0.01" className="form-control" value={categoryForm.max_amount} onChange={(e) => setCategoryForm((p) => ({ ...p, max_amount: e.target.value }))} />
              </div>
              <div className="mb-2">
                <label className="form-label">Category Type</label>
                <select className="form-select" value={categoryForm.category_type} onChange={(e) => setCategoryForm((p) => ({ ...p, category_type: e.target.value }))}>
                  <option value="">-- choose type --</option>
                  {(categoryTypes.length ? categoryTypes : []).map((t) => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div className="form-check mb-2">
                <input className="form-check-input" id="requires_receipt" checked={categoryForm.requires_receipt} onChange={(e) => setCategoryForm((p) => ({ ...p, requires_receipt: e.target.checked }))} />
                <label className="form-check-label" htmlFor="requires_receipt">Requires receipt</label>
              </div>
              <div className="form-check mb-2">
                <input className="form-check-input" id="approval_required" checked={categoryForm.approval_required} onChange={(e) => setCategoryForm((p) => ({ ...p, approval_required: e.target.checked }))} />
                <label className="form-check-label" htmlFor="approval_required">Approval required</label>
              </div>
              <div className="form-check mb-2">
                <input className="form-check-input" id="is_active" checked={categoryForm.is_active} onChange={(e) => setCategoryForm((p) => ({ ...p, is_active: e.target.checked }))} />
                <label className="form-check-label" htmlFor="is_active">Active</label>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" type="button" onClick={() => setShowCategoryModal(false)}>Close</button>
              <button className="btn btn-primary" type="submit" disabled={loading}>{editingCategory ? "Update" : "Create"}</button>
            </div>
          </form>
        </div>
      </div>

      {/* ---------- HISTORY MODAL ---------- */}
      <div
        className={`modal fade ${showHistoryModal ? "d-block" : ""}`}
        tabIndex={-1}
        role="dialog"
        style={{ background: showHistoryModal ? "rgba(0,0,0,0.45)" : undefined }}
        onClick={() => setShowHistoryModal(false)}
      >
        <div className="modal-dialog modal-lg" onClick={(e) => e.stopPropagation()}>
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">Claim History</h5>
              <button type="button" className="btn-close" onClick={() => setShowHistoryModal(false)} />
            </div>
            <div className="modal-body">
              {historyEntries.length === 0 && <div className="text-muted">No history entries.</div>}
              {historyEntries.map((h) => (
                <div key={h.id} className="card mb-2">
                  <div className="card-body">
                    <div className="small text-muted">{h.timestamp || h.created_at}</div>
                    <div className="fw-semibold">{h.previous_status} → {h.new_status}</div>
                    <div className="small">{h.by || h.user_name}</div>
                    <div className="mt-1">{h.notes}</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowHistoryModal(false)}>Close</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
