// src/pages/HROverview.jsx
import React, { useEffect, useRef, useState } from "react";
import HRApi from "../api/hrapi";
import { useAuth } from "../context/AuthContext";

/**
 * HROverview - UI tweaks:
 * - View opens Profile modal (loads documents for that employee)
 * - Removed the small "Employees" summary card
 * - Kept all API calls and existing logic unchanged
 * - Fixed JSX syntax error (Onboard button)
 */

export default function HROverview() {
  const { user, logout } = useAuth();
  const role = (user && user.role) || "employee";
  const adminRoles = ["admin", "hr", "manager"];

  const [profile, setProfile] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [allowedChoices, setAllowedChoices] = useState({ gender: null, marital_status: null });
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createForm, setCreateForm] = useState({
    user_id: "",
    employee_id: "",
    designation: "",
    department: "",
    joining_date: "",
    date_of_birth: "",
    gender: "",
    marital_status: "",
    phone_primary: "",
    email_personal: "",
    current_address: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
    emergency_contact_relation: "",
  });
  const [editingProfileId, setEditingProfileId] = useState(null);
  const [showDocModal, setShowDocModal] = useState(false);
  const [docFile, setDocFile] = useState(null);
  const [docType, setDocType] = useState("");
  const [documentChoices, setDocumentChoices] = useState(null);
  // documents list for current profile (or all for admin in docs modal)
  const [documents, setDocuments] = useState([]);
  const [uploadTargetEmployeeId, setUploadTargetEmployeeId] = useState(null);
  const [showOnboardModal, setShowOnboardModal] = useState(false);
  const [onboardForm, setOnboardForm] = useState({ task_name: "", task_description: "", due_date: "", assigned_to: "", notes: "" });
  const [onboardingTasks, setOnboardingTasks] = useState([]);
  const [selectedOnboardEmployee, setSelectedOnboardEmployee] = useState(null);
  const [showTaskDetailModal, setShowTaskDetailModal] = useState(false);
  const [taskDetail, setTaskDetail] = useState(null);
  const [taskEditForm, setTaskEditForm] = useState({});
  const [showEmploymentModal, setShowEmploymentModal] = useState(false);
  const [employmentRecords, setEmploymentRecords] = useState([]);
  const [selectedEmploymentEmployee, setSelectedEmploymentEmployee] = useState(null);
  const [employmentForm, setEmploymentForm] = useState({ company_name: "", designation: "", start_date: "", end_date: "", is_current: false, job_description: "" });
  const [editingEmploymentId, setEditingEmploymentId] = useState(null);

  // Profile modal visibility
  const [showProfileModal, setShowProfileModal] = useState(false);

  const createdTarget = useRef({ id: null, employee_id: null });
  const tableRef = useRef(null);

  // client-side filters (search hidden for employee/intern)
  const [q, setQ] = useState("");
  const [deptFilter, setDeptFilter] = useState("");
  const [designationFilter, setDesignationFilter] = useState("");
  const [sortBy, setSortBy] = useState("employee_id");

  const fallbackGender = [
    { value: "male", label: "Male" },
    { value: "female", label: "Female" },
    { value: "other", label: "Other" },
  ];
  const fallbackMarital = [
    { value: "single", label: "Single" },
    { value: "married", label: "Married" },
    { value: "divorced", label: "Divorced" },
    { value: "widowed", label: "Widowed" },
  ];

  useEffect(() => {
    let mounted = true;

    async function fetchAllowedChoices() {
      try {
        const res = await HRApi.__axios.options("/api/hr/employees/");
        const postActions = res.data?.actions?.POST || res.data?.actions || res.data;
        const parseChoices = (meta) => {
          if (!meta) return null;
          if (Array.isArray(meta)) {
            return meta
              .map((c) => {
                if (Array.isArray(c) && c.length >= 2) return { value: String(c[0]), label: String(c[1]) };
                if (c && typeof c === "object") return { value: String(c.value ?? c.key ?? ""), label: String(c.display_name ?? c.label ?? c.value ?? "") };
                return null;
              })
              .filter(Boolean);
          }
          if (typeof meta === "object") {
            if (Array.isArray(meta.choices)) {
              return meta.choices.map((c) => ({ value: String(c.value ?? c[0]), label: String(c.display_name ?? c[1] ?? c.value ?? c[0]) }));
            }
            if (meta.choices && typeof meta.choices === "object") {
              return Object.keys(meta.choices).map((k) => ({ value: String(k), label: String(meta.choices[k]) }));
            }
          }
          return null;
        };
        let genderMeta = postActions?.gender ?? res.data?.fields?.gender ?? null;
        let maritalMeta = postActions?.marital_status ?? res.data?.fields?.marital_status ?? null;
        if (!genderMeta && res.data?.actions?.POST) genderMeta = res.data.actions.POST.gender ?? null;
        if (!maritalMeta && res.data?.actions?.POST) maritalMeta = res.data.actions.POST.marital_status ?? null;
        const parsedGender = parseChoices(genderMeta) || null;
        const parsedMarital = parseChoices(maritalMeta) || null;
        if (mounted) {
          setAllowedChoices({ gender: parsedGender?.length ? parsedGender : fallbackGender, marital_status: parsedMarital?.length ? parsedMarital : fallbackMarital });
        }
      } catch (e) {
        if (mounted) setAllowedChoices({ gender: fallbackGender, marital_status: fallbackMarital });
      }
    }

    async function fetchDocumentChoices() {
      try {
        const res = await HRApi.__axios.options("/api/hr/documents/");
        const meta = res.data?.actions?.POST?.document_type ?? res.data?.actions?.POST?.document_type?.choices ?? res.data?.fields?.document_type ?? res.data?.actions?.document_type ?? null;
        const parse = (m) => {
          if (!m) return null;
          if (Array.isArray(m)) {
            return m
              .map((c) => {
                if (Array.isArray(c) && c.length >= 2) return { value: String(c[0]), label: String(c[1]) };
                if (c && typeof c === "object") return { value: String(c.value ?? c.key ?? ""), label: String(c.display_name ?? c.label ?? c.value ?? "") };
                return null;
              })
              .filter(Boolean);
          }
          if (typeof m === "object") {
            if (Array.isArray(m.choices)) {
              return m.choices.map((c) => ({ value: String(c.value ?? c[0]), label: String(c.display_name ?? c[1] ?? c.value ?? c[0]) }));
            }
            if (m.choices && typeof m.choices === "object") {
              return Object.keys(m.choices).map((k) => ({ value: String(k), label: String(m.choices[k]) }));
            }
          }
          return null;
        };
        const parsed = parse(meta) || parse(res.data?.actions?.POST) || null;
        if (mounted) setDocumentChoices(parsed);
      } catch (e) {
        if (mounted) setDocumentChoices(null);
      }
    }

    async function init() {
      await Promise.all([fetchAllowedChoices(), fetchDocumentChoices()]);
      if (!mounted) return;
      try {
        setLoading(true);
        try {
          const res = await HRApi.fetchMyProfile();
          setProfile(res.data);
        } catch {
          setProfile(null);
        }
        try {
          const r = await HRApi.fetchEmployees();
          setEmployees(r.data?.results || r.data || []);
        } catch (_) {}
      } finally {
        setLoading(false);
      }
    }

    init();
    return () => {
      mounted = false;
    };
  }, []);

  // load documents for the selected profile automatically
  useEffect(() => {
    if (profile?.id) {
      loadDocumentsForProfile(profile.id);
    } else {
      setDocuments([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile?.id]);

  function isE164(v) {
    return /^\+\d{10,15}$/.test(v || "");
  }

  function showValidation(err) {
    const data = err?.response?.data;
    if (!data) {
      alert(err?.message || "Server error");
      return;
    }
    if (data.detail) {
      alert(data.detail);
      return;
    }
    if (typeof data === "object") {
      const msgs = [];
      Object.keys(data).forEach((k) => {
        const val = data[k];
        if (Array.isArray(val)) msgs.push(`${k}: ${val.join(", ")}`);
        else msgs.push(`${k}: ${String(val)}`);
      });
      alert(msgs.join("\n"));
    } else alert(String(data));
  }

  function canCreate() {
    return adminRoles.includes(role);
  }

  function canEdit(emp) {
    if (!emp) return adminRoles.includes(role);
    if (emp.user && user && emp.user.id === user.id) return true;
    return adminRoles.includes(role);
  }

  function handleCreateChange(e) {
    const { name, value, type, checked } = e.target;
    setCreateForm((p) => ({ ...p, [name]: type === "checkbox" ? checked : value }));
  }

  function handleDocFileChange(e) {
    setDocFile(e.target.files[0] || null);
  }

  async function loadDocumentsForProfile(employeeId) {
    if (!employeeId) {
      setDocuments([]);
      return;
    }
    try {
      const res = await HRApi.__axios.get("/api/hr/documents/", { params: { employee: employeeId } });
      setDocuments(res.data?.results || res.data || []);
    } catch (err) {
      console.error("loadDocumentsForProfile error", err);
      setDocuments([]);
    }
  }

  async function loadAllDocuments() {
    try {
      const res = await HRApi.__axios.get("/api/hr/documents/");
      setDocuments(res.data?.results || res.data || []);
    } catch (err) {
      console.error("loadAllDocuments error", err);
      setDocuments([]);
    }
  }

  const openDocModal = async () => {
    if (!profile?.id && !["admin", "hr"].includes(role)) {
      alert("Open your profile (or contact admin) before uploading documents.");
      return;
    }
    if (["admin", "hr"].includes(role)) {
      await loadAllDocuments();
      setUploadTargetEmployeeId(profile?.id || null);
      setShowDocModal(true);
      return;
    }
    if (["employee", "intern", "manager"].includes(role)) {
      if (profile?.user?.id !== user?.id) {
        alert("You can only manage documents for your own profile.");
        return;
      }
      await loadDocumentsForProfile(profile.id);
      setUploadTargetEmployeeId(profile.id);
      setShowDocModal(true);
      return;
    }
    await loadAllDocuments();
    setShowDocModal(true);
  };

  async function uploadDocument(e) {
    e.preventDefault();
    const targetEmpId = uploadTargetEmployeeId || profile?.id;
    if (!targetEmpId) {
      alert("Select a profile to upload for.");
      return;
    }
    if (!["admin", "hr"].includes(role)) {
      if (targetEmpId !== profile?.id) {
        alert("You can only upload documents for your own profile.");
        return;
      }
    }
    if (!docFile) {
      alert("Please choose a file to upload.");
      return;
    }

    setLoading(true);
    try {
      const fd = new FormData();
      fd.append("employee", targetEmpId);
      if (docType) fd.append("document_type", docType);
      fd.append("document_file", docFile);
      await HRApi.__axios.post("/api/hr/documents/", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (ev) => {
          const pct = ev.total ? Math.round((ev.loaded * 100) / ev.total) : 0;
          setUploadProgress(pct);
        },
      });
      alert("Document uploaded successfully.");
      setDocFile(null);
      setDocType("");
      setShowDocModal(true);
      if (["admin", "hr"].includes(role)) {
        await loadAllDocuments();
      } else {
        await loadDocumentsForProfile(profile.id);
      }
      try {
        const r = await HRApi.fetchEmployees();
        setEmployees(r.data?.results || r.data || []);
      } catch (_) {}
      try {
        const p = await HRApi.fetchMyProfile();
        setProfile(p.data);
      } catch (_) {}
    } catch (err) {
      console.error("uploadDocument error", err);
      if (err.response?.status === 401) {
        alert("Authentication required. Please login again.");
        logout();
        return;
      }
      showValidation(err);
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  }

  async function verifyDocument(docId) {
    if (!["admin", "hr"].includes(role)) {
      alert("Only Admin/HR can verify documents.");
      return;
    }
    if (!window.confirm("Verify this document?")) return;
    try {
      await HRApi.__axios.post(`/api/hr/documents/${docId}/verify/`);
      alert("Document verified.");
      if (["admin", "hr"].includes(role)) await loadAllDocuments();
      else if (profile?.id) await loadDocumentsForProfile(profile.id);
    } catch (err) {
      console.error("verifyDocument error", err);
      if (err.response?.status === 401) {
        alert("Authentication required. Please login again.");
        logout();
        return;
      }
      showValidation(err);
    }
  }

  async function deleteDocument(docId) {
    if (!window.confirm("Delete this document? This action cannot be undone.")) return;
    try {
      await HRApi.__axios.delete(`/api/hr/documents/${docId}/`);
      alert("Document deleted.");
      if (["admin", "hr"].includes(role)) await loadAllDocuments();
      else if (profile?.id) await loadDocumentsForProfile(profile.id);
    } catch (err) {
      console.error("deleteDocument error", err);
      if (err.response?.status === 401) {
        alert("Authentication required. Please login again.");
        logout();
        return;
      }
      showValidation(err);
    }
  }

  function canDeleteDocument(d) {
    if (!d) return false;
    if (["admin", "hr"].includes(role)) return true;
    if (d.uploaded_by && user && Number(d.uploaded_by) === Number(user.id)) return true;
    if (d.uploaded_by_email && user && d.uploaded_by_email === user.email) return true;
    if (d.uploaded_by_user && d.uploaded_by_user.id && user && Number(d.uploaded_by_user.id) === Number(user.id)) return true;
    if (d.employee && profile && Number(d.employee.id) === Number(profile.id)) return true;
    return false;
  }

  function handleOnboardChange(e) {
    const { name, value } = e.target;
    setOnboardForm((p) => ({ ...p, [name]: value }));
  }

  async function createOnboardingTask(e) {
    e.preventDefault();
    if (!["admin", "hr"].includes(role)) {
      alert("Only Admin/HR can create onboarding tasks.");
      setShowOnboardModal(false);
      return;
    }
    if (!selectedOnboardEmployee) {
      alert("Please select an employee for this onboarding task.");
      return;
    }
    if (!onboardForm.task_name || !onboardForm.due_date) {
      alert("Please provide task name and due date.");
      return;
    }
    setLoading(true);
    try {
      const payload = { employee: Number(selectedOnboardEmployee), task_name: onboardForm.task_name, task_description: onboardForm.task_description || "", due_date: onboardForm.due_date };
      if (onboardForm.assigned_to) {
        const assignedPk = Number(onboardForm.assigned_to);
        if (!Number.isInteger(assignedPk) || assignedPk <= 0) {
          alert("Assigned To must be a valid user id selection.");
          setLoading(false);
          return;
        }
        payload.assigned_to = assignedPk;
      }
      if (onboardForm.notes) payload.notes = onboardForm.notes;
      await HRApi.__axios.post("/api/hr/onboarding/", payload, { headers: { "Content-Type": "application/json" } });
      alert("Onboarding task created.");
      setShowOnboardModal(false);
      setOnboardForm({ task_name: "", task_description: "", due_date: "", assigned_to: "", notes: "" });
      await fetchOnboardingTasks(selectedOnboardEmployee);
    } catch (err) {
      console.error("createOnboardingTask error", err);
      if (err.response?.status === 401) {
        alert("Authentication required. Please login again.");
        logout();
        return;
      }
      showValidation(err);
    } finally {
      setLoading(false);
    }
  }

  async function fetchOnboardingTasks(employeeId) {
    if (!employeeId) {
      setOnboardingTasks([]);
      return;
    }
    try {
      const res = await HRApi.__axios.get("/api/hr/onboarding/", { params: { employee: employeeId } });
      setOnboardingTasks(res.data?.results || res.data || []);
    } catch (err) {
      console.error("fetchOnboardingTasks error", err);
      setOnboardingTasks([]);
    }
  }

  async function getOnboardingTaskDetail(id) {
    try {
      const res = await HRApi.__axios.get(`/api/hr/onboarding/${id}/`);
      setTaskDetail(res.data);
      setTaskEditForm(res.data || {});
      setShowTaskDetailModal(true);
    } catch (err) {
      console.error("getOnboardingTaskDetail error", err);
      showValidation(err);
    }
  }

  async function updateOnboardingTask(id, changes) {
    try {
      const res = await HRApi.__axios.patch(`/api/hr/onboarding/${id}/`, changes);
      alert("Task updated.");
      setTaskDetail(res.data);
      setShowTaskDetailModal(false);
      if (selectedOnboardEmployee) await fetchOnboardingTasks(selectedOnboardEmployee);
    } catch (err) {
      console.error("updateOnboardingTask error", err);
      showValidation(err);
    }
  }

  async function putOnboardingTask(id, payload) {
    try {
      const res = await HRApi.__axios.put(`/api/hr/onboarding/${id}/`, payload);
      alert("Task fully updated.");
      setTaskDetail(res.data);
      setShowTaskDetailModal(false);
      if (selectedOnboardEmployee) await fetchOnboardingTasks(selectedOnboardEmployee);
    } catch (err) {
      console.error("putOnboardingTask error", err);
      showValidation(err);
    }
  }

  async function deleteOnboardingTask(id) {
    if (!window.confirm("Delete this onboarding task?")) return;
    try {
      await HRApi.__axios.delete(`/api/hr/onboarding/${id}/`);
      alert("Task deleted.");
      if (selectedOnboardEmployee) await fetchOnboardingTasks(selectedOnboardEmployee);
    } catch (err) {
      console.error("deleteOnboardingTask error", err);
      showValidation(err);
    }
  }

  async function completeOnboardingTask(id, notes = "") {
    try {
      const payload = notes ? { notes } : {};
      await HRApi.__axios.post(`/api/hr/onboarding/${id}/complete/`, payload);
      alert("Task marked complete.");
      if (selectedOnboardEmployee) await fetchOnboardingTasks(selectedOnboardEmployee);
    } catch (err) {
      console.error("completeOnboardingTask error", err);
      showValidation(err);
    }
  }

  async function fetchEmploymentHistory(employeeId) {
    if (!employeeId) {
      setEmploymentRecords([]);
      return;
    }
    try {
      const res = await HRApi.__axios.get("/api/hr/employment-history/", { params: { employee: employeeId } });
      setEmploymentRecords(res.data?.results || res.data || []);
    } catch (err) {
      console.error("fetchEmploymentHistory error", err);
      setEmploymentRecords([]);
    }
  }

  async function addEmploymentRecord(payload) {
    try {
      const res = await HRApi.__axios.post("/api/hr/employment-history/", payload, { headers: { "Content-Type": "application/json" } });
      alert("Employment record added.");
      if (selectedEmploymentEmployee) await fetchEmploymentHistory(selectedEmploymentEmployee);
      return res.data;
    } catch (err) {
      console.error("addEmploymentRecord error", err);
      showValidation(err);
    }
  }

  async function editEmploymentRecord(id, changes) {
    try {
      const res = await HRApi.__axios.patch(`/api/hr/employment-history/${id}/`, changes, { headers: { "Content-Type": "application/json" } });
      alert("Employment record updated.");
      if (selectedEmploymentEmployee) await fetchEmploymentHistory(selectedEmploymentEmployee);
      return res.data;
    } catch (err) {
      console.error("editEmploymentRecord error", err);
      showValidation(err);
    }
  }

  async function deleteEmploymentRecord(id) {
    if (!window.confirm("Delete this employment record?")) return;
    try {
      await HRApi.__axios.delete(`/api/hr/employment-history/${id}/`);
      alert("Employment record deleted.");
      if (selectedEmploymentEmployee) await fetchEmploymentHistory(selectedEmploymentEmployee);
    } catch (err) {
      console.error("deleteEmploymentRecord error", err);
      showValidation(err);
    }
  }

  async function createProfile(e) {
    e.preventDefault();
    const isEditing = Boolean(editingProfileId);
    if (!adminRoles.includes(role)) {
      alert("Only Admin/HR/Manager can create or edit profiles.");
      setShowCreateModal(false);
      return;
    }
    const required = [
      "user_id",
      "employee_id",
      "designation",
      "department",
      "joining_date",
      "date_of_birth",
      "gender",
      "marital_status",
      "phone_primary",
      "email_personal",
      "current_address",
      "emergency_contact_name",
      "emergency_contact_phone",
      "emergency_contact_relation",
    ];
    for (const key of required) {
      if (!createForm[key] || String(createForm[key]).trim() === "") {
        alert(`Please provide ${key.replace(/_/g, " ")} (required).`);
        return;
      }
    }
    if (!isE164(createForm.phone_primary) || !isE164(createForm.emergency_contact_phone)) {
      alert("Phone numbers must be in E.164 format (e.g. +919876543210).");
      return;
    }
    const maybeInt = Number(createForm.user_id);
    if (!Number.isInteger(maybeInt) || maybeInt <= 0) {
      alert("user_id must be a valid positive integer.");
      return;
    }
    const userIdToSend = String(maybeInt);
    setLoading(true);
    setUploadProgress(0);
    try {
      const fd = new FormData();
      fd.append("user_id", userIdToSend);
      Object.keys(createForm).forEach((k) => {
        if (k === "user_id") return;
        fd.append(k, createForm[k]);
      });

      let res;
      if (isEditing) {
        res = await HRApi.__axios.put(`/api/hr/employees/${editingProfileId}/`, fd, {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (ev) => {
            const pct = ev.total ? Math.round((ev.loaded * 100) / ev.total) : 0;
            setUploadProgress(pct);
          },
        });
      } else {
        res = await HRApi.__axios.post(`/api/hr/employees/`, fd, {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: (ev) => {
            const pct = ev.total ? Math.round((ev.loaded * 100) / ev.total) : 0;
            setUploadProgress(pct);
          },
        });
      }

      const created = res.data || {};
      createdTarget.current = { id: created.id || null, employee_id: created.employee_id || createForm.employee_id };
      setShowCreateModal(false);
      setEditingProfileId(null);
      await refreshEmployeesAndScroll(createdTarget.current);
      setCreateForm({
        user_id: "",
        employee_id: "",
        designation: "",
        department: "",
        joining_date: "",
        date_of_birth: "",
        gender: "",
        marital_status: "",
        phone_primary: "",
        email_personal: "",
        current_address: "",
        emergency_contact_name: "",
        emergency_contact_phone: "",
        emergency_contact_relation: "",
      });
      alert(isEditing ? "Profile updated successfully." : "Profile created successfully.");
    } catch (err) {
      console.error("createProfile error", err);
      if (err.response?.status === 401) {
        alert("Authentication required. Please login again.");
        logout();
        return;
      }
      showValidation(err);
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  }

  async function refreshEmployeesAndScroll(target) {
    try {
      const r = await HRApi.fetchEmployees();
      const list = r.data?.results || r.data || [];
      setEmployees(list);
      setTimeout(() => {
        try {
          let rowEl = null;
          if (target.id) rowEl = document.querySelector(`[data-emp-id="${target.id}"]`);
          if (!rowEl && target.employee_id) rowEl = document.querySelector(`[data-emp-eid="${CSS.escape(target.employee_id)}"]`);
          if (rowEl) {
            rowEl.scrollIntoView({ behavior: "smooth", block: "center" });
            rowEl.classList.add("bg-warning");
            setTimeout(() => rowEl.classList.remove("bg-warning"), 1600);
          } else {
            if (tableRef.current) tableRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
          }
        } catch (e) {}
      }, 120);
    } catch (err) {
      console.error("refreshEmployees failed", err);
    }
  }

  // viewEmployee now opens modal and loads documents via useEffect(profile.id)
  async function viewEmployee(empId) {
    try {
      const res = await HRApi.getEmployee(empId);
      setProfile(res.data);
      setShowProfileModal(true);
    } catch (err) {
      showValidation(err);
    }
  }

  function handleEdit(emp) {
    setEditingProfileId(emp.id || null);
    setCreateForm({
      user_id: emp.user?.id || "",
      employee_id: emp.employee_id || "",
      designation: emp.designation || "",
      department: emp.department || "",
      joining_date: emp.joining_date || "",
      date_of_birth: emp.date_of_birth || "",
      gender: emp.gender || "",
      marital_status: emp.marital_status || "",
      phone_primary: emp.phone_primary || "",
      email_personal: emp.email_personal || "",
      current_address: emp.current_address || "",
      emergency_contact_name: emp.emergency_contact_name || "",
      emergency_contact_phone: emp.emergency_contact_phone || "",
      emergency_contact_relation: emp.emergency_contact_relation || "",
    });
    setProfile(emp);
    setShowCreateModal(true);
  }

  async function handleDelete(empId) {
    if (!window.confirm("Delete this employee?")) return;
    try {
      await HRApi.deleteEmployee(empId);
      alert("Deleted");
      const r = await HRApi.fetchEmployees();
      setEmployees(r.data?.results || r.data || []);
    } catch (err) {
      showValidation(err);
    }
  }

  const genderOptionsToRender = allowedChoices.gender || fallbackGender;
  const maritalOptionsToRender = allowedChoices.marital_status || fallbackMarital;
  const docChoicesToRender = documentChoices || null;

  const modalBackdropProps = {
    onClick: (e) => {
      if (e.target === e.currentTarget) {
        if (showDocModal) setShowDocModal(false);
        if (showCreateModal) {
          setShowCreateModal(false);
          setEditingProfileId(null);
        }
        if (showOnboardModal) setShowOnboardModal(false);
        if (showTaskDetailModal) setShowTaskDetailModal(false);
        if (showEmploymentModal) setShowEmploymentModal(false);
        if (showProfileModal) setShowProfileModal(false);
      }
    },
  };

  const openOnboardingFor = async (emp) => {
    const eid = emp?.id || null;
    if (!eid) {
      alert("Employee missing");
      return;
    }
    setSelectedOnboardEmployee(eid);
    await fetchOnboardingTasks(eid);
    setShowOnboardModal(true);
  };

  const openEmploymentFor = async (emp) => {
    const eid = emp?.id || null;
    if (!eid) {
      alert("Employee missing");
      return;
    }
    setSelectedEmploymentEmployee(eid);
    await fetchEmploymentHistory(eid);
    setShowEmploymentModal(true);
  };

  function handleTaskEditChange(e) {
    const { name, value } = e.target;
    setTaskEditForm((p) => ({ ...p, [name]: value }));
  }

  function handleEmploymentChange(e) {
    const { name, value, type, checked } = e.target;
    setEmploymentForm((p) => ({ ...p, [name]: type === "checkbox" ? checked : value }));
  }

  async function handleEmploymentSave(e) {
    e.preventDefault();
    const payload = { ...employmentForm, employee: selectedEmploymentEmployee };
    if (!payload.company_name || !payload.start_date) {
      alert("Please provide company and start date.");
      return;
    }
    setLoading(true);
    try {
      if (editingEmploymentId) {
        await editEmploymentRecord(editingEmploymentId, payload);
        setEditingEmploymentId(null);
      } else {
        await addEmploymentRecord(payload);
      }
      setEmploymentForm({ company_name: "", designation: "", start_date: "", end_date: "", is_current: false, job_description: "" });
      await fetchEmploymentHistory(selectedEmploymentEmployee);
    } catch (err) {
      console.error("handleEmploymentSave error", err);
    } finally {
      setLoading(false);
    }
  }

  function startEditEmployment(rec) {
    setEditingEmploymentId(rec.id);
    setEmploymentForm({ company_name: rec.company_name || "", designation: rec.designation || "", start_date: rec.start_date || "", end_date: rec.end_date || "", is_current: !!rec.is_current, job_description: rec.job_description || "" });
  }

  function assignedToLabel(t) {
    if (t.assigned_to_user && (t.assigned_to_user.email || t.assigned_to_user.first_name || t.assigned_to_user.last_name)) {
      if (t.assigned_to_user.email) return `${t.assigned_to_user.email} (${t.assigned_to_user.first_name || ""} ${t.assigned_to_user.last_name || ""})`.trim();
      return `${t.assigned_to_user.first_name || ""} ${t.assigned_to_user.last_name || ""}`.trim();
    }
    if (t.assigned_to_email) return t.assigned_to_email;
    if (t.assigned_to) return String(t.assigned_to);
    return "-";
  }

  function assignedToMatchesCurrentUser(t) {
    if (!user) return false;
    const uid = Number(user.id);
    if (t.assigned_to_user && Number(t.assigned_to_user.id) === uid) return true;
    if (t.assigned_to && Number(t.assigned_to) === uid) return true;
    if (t.assigned_to === user.email) return true;
    if (t.assigned_to_email === user.email) return true;
    return false;
  }

  const distinctDepartments = Array.from(new Set(employees.map((e) => e.department).filter(Boolean))).sort();
  const distinctDesignations = Array.from(new Set(employees.map((e) => e.designation).filter(Boolean))).sort();

  const filteredEmployees = employees
    .filter((emp) => {
      if (q) {
        const ql = q.toLowerCase();
        const name = `${emp.user?.first_name || ""} ${emp.user?.last_name || ""}`.toLowerCase();
        if (!(name.includes(ql) || String(emp.employee_id || "").toLowerCase().includes(ql) || String(emp.user?.email || "").toLowerCase().includes(ql))) return false;
      }
      if (deptFilter && emp.department !== deptFilter) return false;
      if (designationFilter && emp.designation !== designationFilter) return false;
      return true;
    })
    .sort((a, b) => {
      if (sortBy === "employee_id") return String(a.employee_id || "").localeCompare(String(b.employee_id || ""));
      if (sortBy === "name") {
        const an = `${a.user?.first_name || ""} ${a.user?.last_name || ""}`.trim();
        const bn = `${b.user?.first_name || ""} ${b.user?.last_name || ""}`.trim();
        return an.localeCompare(bn);
      }
      return 0;
    });

  return (
    <div className="container py-4">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h1 className="h4 mb-0">HR Overview</h1>
          <div className="small text-muted">Employee directory, docs, onboarding & history</div>
        </div>

        <div className="d-flex gap-2">
          {adminRoles.includes(role) && (
            <button
              className="btn btn-primary"
              onClick={() => {
                setProfile(null);
                setCreateForm({
                  user_id: "",
                  employee_id: "",
                  designation: "",
                  department: "",
                  joining_date: "",
                  date_of_birth: "",
                  gender: "",
                  marital_status: "",
                  phone_primary: "",
                  email_personal: "",
                  current_address: "",
                  emergency_contact_name: "",
                  emergency_contact_phone: "",
                  emergency_contact_relation: "",
                });
                setEditingProfileId(null);
                setShowCreateModal(true);
              }}
            >
              + Create Profile
            </button>
          )}

          {["admin", "hr"].includes(role) && (
            <button
              className="btn btn-outline-success"
              onClick={() => {
                setSelectedOnboardEmployee(null);
                setOnboardForm({ task_name: "", task_description: "", due_date: "", assigned_to: "", notes: "" });
                setShowOnboardModal(true);
              }}
            >
              + Onboard Task
            </button>
          )}

          {((adminRoles.includes(role)) || (profile?.user?.id === user?.id) || ["employee", "intern"].includes(role)) && (
            <button className="btn btn-outline-primary" onClick={() => openDocModal()}>
              Upload Document
            </button>
          )}
        </div>
      </div>

      {/* Controls: show search only for roles that are NOT employee/intern */}
      {!["employee", "intern"].includes(role) && (
        <div className="card mb-3">
          <div className="card-body d-flex flex-column flex-md-row gap-2 align-items-center">
            <div className="flex-grow-1 w-100">
              <input className="form-control" placeholder="Search name, employee id or email..." value={q} onChange={(e) => setQ(e.target.value)} />
            </div>

            <div className="d-flex gap-2 align-items-center">
              <select className="form-select" value={deptFilter} onChange={(e) => setDeptFilter(e.target.value)}>
                <option value="">All departments</option>
                {distinctDepartments.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>

              <select className="form-select" value={designationFilter} onChange={(e) => setDesignationFilter(e.target.value)}>
                <option value="">All designations</option>
                {distinctDesignations.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>

              <select className="form-select" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                <option value="employee_id">Sort: Employee ID</option>
                <option value="name">Sort: Name</option>
              </select>

              <button className="btn btn-outline-secondary" onClick={() => { setQ(""); setDeptFilter(""); setDesignationFilter(""); setSortBy("employee_id"); }}>
                Reset
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Employees table */}
      <div ref={tableRef} className="table-responsive mb-4">
        <table className="table table-hover align-middle">
          <thead className="table-light">
            <tr>
              <th>#</th>
              <th>Employee ID</th>
              <th>Name</th>
              <th>Designation</th>
              <th>Department</th>
              <th className="text-end">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredEmployees.length === 0 && (
              <tr>
                <td colSpan={6} className="text-center text-muted py-4">
                  {loading ? "Loading employees..." : "No employees found."}
                </td>
              </tr>
            )}

            {filteredEmployees.map((emp, idx) => (
              <tr key={emp.id || emp.employee_id} data-emp-id={emp.id} data-emp-eid={emp.employee_id}>
                <td style={{ width: 50 }}>{idx + 1}</td>
                <td style={{ minWidth: 140 }}>
                  <div className="fw-semibold">{emp.employee_id}</div>
                  <div className="small text-muted">{emp.user?.email}</div>
                </td>
                <td>
                  <div>{emp.user?.first_name} {emp.user?.last_name}</div>
                </td>
                <td>{emp.designation || "—"}</td>
                <td>{emp.department || "—"}</td>
                <td className="text-end">
                  <div className="d-flex justify-content-end flex-wrap gap-1">
                    <button className="btn btn-sm btn-outline-primary" onClick={() => viewEmployee(emp.id)}>View</button>

                    {canEdit(emp) && (
                      <button className="btn btn-sm btn-outline-warning" onClick={() => handleEdit(emp)}>
                        Edit
                      </button>
                    )}

                    {adminRoles.includes(role) && (
                      <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(emp.id)}>
                        Delete
                      </button>
                    )}

                    <button className="btn btn-sm btn-outline-secondary" onClick={() => openEmploymentFor(emp)}>History</button>

                    <button className="btn btn-sm btn-outline-success" onClick={() => openOnboardingFor(emp)}>Onboard</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create/Edit Profile Modal */}
      {showCreateModal && (
        <div className="modal show d-block" tabIndex="-1" {...modalBackdropProps} style={{ background: "rgba(0,0,0,0.45)" }}>
          <div className="modal-dialog modal-lg">
            <form className="modal-content" onSubmit={createProfile}>
              <div className="modal-header">
                <h5 className="modal-title">{editingProfileId ? "Edit Profile" : "Create Profile"}</h5>
                <button type="button" className="btn-close" onClick={() => { setShowCreateModal(false); setEditingProfileId(null); }}></button>
              </div>
              <div className="modal-body">
                <div className="row g-3">
                  <div className="col-md-6">
                    <label className="form-label">User ID (required)</label>
                    <input type="number" min="1" name="user_id" className="form-control" value={createForm.user_id} onChange={handleCreateChange} required />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label">Employee ID</label>
                    <input type="text" name="employee_id" className="form-control" value={createForm.employee_id} onChange={handleCreateChange} required />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label">Designation</label>
                    <input type="text" name="designation" className="form-control" value={createForm.designation} onChange={handleCreateChange} required />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label">Department</label>
                    <input type="text" name="department" className="form-control" value={createForm.department} onChange={handleCreateChange} required />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label">Joining Date</label>
                    <input type="date" name="joining_date" className="form-control" value={createForm.joining_date} onChange={handleCreateChange} required />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label">Date of Birth</label>
                    <input type="date" name="date_of_birth" className="form-control" value={createForm.date_of_birth} onChange={handleCreateChange} required />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label">Gender</label>
                    <select className="form-select" name="gender" value={createForm.gender} onChange={handleCreateChange} required>
                      <option value="">Select Gender</option>
                      {genderOptionsToRender?.map((g) => (
                        <option key={g.value} value={g.value}>
                          {g.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="col-md-6">
                    <label className="form-label">Marital Status</label>
                    <select className="form-select" name="marital_status" value={createForm.marital_status} onChange={handleCreateChange} required>
                      <option value="">Select Marital Status</option>
                      {maritalOptionsToRender?.map((m) => (
                        <option key={m.value} value={m.value}>
                          {m.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="col-md-6">
                    <label className="form-label">Primary Phone (+E.164)</label>
                    <input type="text" name="phone_primary" className="form-control" value={createForm.phone_primary} onChange={handleCreateChange} required />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label">Personal Email</label>
                    <input type="email" name="email_personal" className="form-control" value={createForm.email_personal} onChange={handleCreateChange} required />
                  </div>

                  <div className="col-12">
                    <label className="form-label">Current Address</label>
                    <textarea className="form-control" name="current_address" value={createForm.current_address} onChange={handleCreateChange} required></textarea>
                  </div>

                  <div className="col-md-4">
                    <label className="form-label">Emergency Contact Name</label>
                    <input type="text" name="emergency_contact_name" className="form-control" value={createForm.emergency_contact_name} onChange={handleCreateChange} required />
                  </div>

                  <div className="col-md-4">
                    <label className="form-label">Emergency Contact Phone (+E.164)</label>
                    <input type="text" name="emergency_contact_phone" className="form-control" value={createForm.emergency_contact_phone} onChange={handleCreateChange} required />
                  </div>

                  <div className="col-md-4">
                    <label className="form-label">Emergency Contact Relation</label>
                    <input type="text" name="emergency_contact_relation" className="form-control" value={createForm.emergency_contact_relation} onChange={handleCreateChange} required />
                  </div>
                </div>

                {uploadProgress > 0 && (
                  <div className="progress my-3">
                    <div className="progress-bar" role="progressbar" style={{ width: `${uploadProgress}%` }}>
                      {uploadProgress}%
                    </div>
                  </div>
                )}
              </div>

              <div className="modal-footer">
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {editingProfileId ? "Update Profile" : "Save Profile"}
                </button>
                <button type="button" className="btn btn-secondary" onClick={() => { setShowCreateModal(false); setEditingProfileId(null); }}>
                  Close
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Profile Modal */}
      {showProfileModal && profile && (
        <div className="modal show d-block" tabIndex="-1" {...modalBackdropProps} style={{ background: "rgba(0,0,0,0.45)" }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Employee Profile — {profile.employee_id || "-"}</h5>
                <button type="button" className="btn-close" onClick={() => setShowProfileModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="row g-3">
                  <div className="col-md-6">
                    <div className="fw-semibold">Name</div>
                    <div>{profile.user?.first_name} {profile.user?.last_name}</div>
                  </div>
                  <div className="col-md-6">
                    <div className="fw-semibold">Email</div>
                    <div>{profile.user?.email || profile.email_personal || "-"}</div>
                  </div>

                  <div className="col-md-6">
                    <div className="fw-semibold">Designation</div>
                    <div>{profile.designation || "-"}</div>
                  </div>
                  <div className="col-md-6">
                    <div className="fw-semibold">Department</div>
                    <div>{profile.department || "-"}</div>
                  </div>

                  <div className="col-md-4">
                    <div className="fw-semibold">Joining Date</div>
                    <div>{profile.joining_date || "-"}</div>
                  </div>
                  <div className="col-md-4">
                    <div className="fw-semibold">DOB</div>
                    <div>{profile.date_of_birth || "-"}</div>
                  </div>
                  <div className="col-md-4">
                    <div className="fw-semibold">Phone</div>
                    <div>{profile.phone_primary || "-"}</div>
                  </div>

                  <div className="col-12">
                    <div className="fw-semibold">Current Address</div>
                    <div className="small text-muted">{profile.current_address || "-"}</div>
                  </div>

                  <div className="col-12 mt-2">
                    <h6 className="mb-3">Documents</h6>
                    {documents.length === 0 ? (
                      <div className="text-muted">No documents found for this employee.</div>
                    ) : (
                      documents.map((d) => (
                        <div key={d.id} className="card mb-2">
                          <div className="card-body d-flex justify-content-between align-items-start">
                            <div>
                              <div className="fw-semibold">{d.document_type || d.document_file_name || "Document"}</div>
                              <div className="small text-muted">{d.document_file_name || d.document_file}</div>
                              <div className="small text-muted">Uploaded: {d.uploaded_at || d.created_at || "-"}</div>
                              {d.is_verified && <div className="small text-success mt-1">Verified</div>}
                            </div>
                            <div className="text-end">
                              <div className="btn-group">
                                <a className="btn btn-sm btn-outline-primary" href={d.document_file} target="_blank" rel="noreferrer">View</a>
                                {canDeleteDocument(d) && <button className="btn btn-sm btn-outline-danger" onClick={() => deleteDocument(d.id)}>Delete</button>}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                {canEdit(profile) && <button className="btn btn-warning" onClick={() => { setShowProfileModal(false); handleEdit(profile); }}>Edit</button>}
                <button className="btn btn-secondary" onClick={() => setShowProfileModal(false)}>Close</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Documents Modal */}
      {showDocModal && (
        <div className="modal show d-block" tabIndex="-1" {...modalBackdropProps} style={{ background: "rgba(0,0,0,0.45)" }}>
          <div className="modal-dialog modal-lg">
            <form className="modal-content" onSubmit={uploadDocument}>
              <div className="modal-header">
                <h5 className="modal-title">Upload / Manage Documents</h5>
                <button type="button" className="btn-close" onClick={() => setShowDocModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-3">
                  <div className="row g-2 align-items-end">
                    {["admin", "hr"].includes(role) && (
                      <div className="col-md-5">
                        <label className="form-label">Upload For (Employee)</label>
                        <select className="form-select" value={uploadTargetEmployeeId || ""} onChange={(e) => setUploadTargetEmployeeId(e.target.value || null)}>
                          <option value="">-- select employee (optional) --</option>
                          {employees.map((emp) => (
                            <option key={emp.id} value={emp.id}>
                              {emp.employee_id} — {emp.user?.first_name} {emp.user?.last_name}
                            </option>
                          ))}
                        </select>
                        <div className="form-text">Leave blank to attach to currently selected profile (if any).</div>
                      </div>
                    )}

                    {!["admin", "hr"].includes(role) && (
                      <div className="col-md-5">
                        <label className="form-label">Upload For</label>
                        <input type="text" readOnly className="form-control" value={profile ? `${profile.employee_id} — ${profile.user?.first_name} ${profile.user?.last_name}` : "Open your profile first"} />
                      </div>
                    )}

                    <div className="col-md-4">
                      <label className="form-label">Document Type</label>
                      <select className="form-select" value={docType} onChange={(e) => setDocType(e.target.value)} required>
                        <option value="">Select Document Type</option>
                        {docChoicesToRender?.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="col-md-3">
                      <label className="form-label">File</label>
                      <input type="file" className="form-control" onChange={handleDocFileChange} required />
                    </div>

                    <div className="col-md-12 text-end mt-2">
                      <button type="submit" className="btn btn-primary" disabled={loading || !docFile}>
                        Upload
                      </button>
                    </div>
                  </div>
                </div>

                {uploadProgress > 0 && (
                  <div className="progress mb-3">
                    <div className="progress-bar" role="progressbar" style={{ width: `${uploadProgress}%` }}>
                      {uploadProgress}%
                    </div>
                  </div>
                )}

                <div>
                  <h6 className="mb-3">Uploaded Documents</h6>
                  {documents.length === 0 && <div className="text-muted">No documents found.</div>}
                  {documents.map((d) => (
                    <div key={d.id} className="card mb-2">
                      <div className="card-body d-flex justify-content-between align-items-start">
                        <div>
                          <div className="fw-semibold">{d.document_type || d.document_file_name || "Document"}</div>
                          <div className="small text-muted">{d.document_file_name || d.document_file}</div>
                          <div className="small text-muted">Uploaded: {d.uploaded_at || d.created_at || "-"}</div>
                          {["admin", "hr"].includes(role) && d.employee && (
                            <div className="small text-muted">Employee: {d.employee.employee_id} — {d.employee.user?.first_name} {d.employee.user?.last_name}</div>
                          )}
                          {d.uploaded_by && <div className="small text-muted">Uploaded by: {d.uploaded_by_email || d.uploaded_by}</div>}
                          {d.is_verified && (<div className="small text-success mt-1">Verified by: {d.verified_by_name || d.verified_by_email || "-"} at {d.verified_at || "-"}</div>)}
                        </div>

                        <div className="text-end">
                          <div className="btn-group mb-2" role="group">
                            <a className="btn btn-sm btn-outline-primary" href={d.document_file} target="_blank" rel="noreferrer">View</a>
                            {canDeleteDocument(d) && (
                              <button className="btn btn-sm btn-outline-danger" onClick={(ev) => { ev.preventDefault(); deleteDocument(d.id); }}>
                                Delete
                              </button>
                            )}
                          </div>

                          <div>
                            {['admin', 'hr'].includes(role) && (
                              <button className="btn btn-sm btn-success" onClick={(ev) => { ev.preventDefault(); verifyDocument(d.id); }} disabled={Boolean(d.is_verified)} style={{ minWidth: 90 }}>
                                {d.is_verified ? "Verified" : "Verify"}
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowDocModal(false)}>Close</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Onboard / TaskDetail / Employment modals unchanged (rendering code omitted here for brevity in this comment) */}
      {/* They are included above in full; kept behavior unchanged. */}

      {showOnboardModal && (
        <div className="modal show d-block" tabIndex="-1" {...modalBackdropProps} style={{ background: "rgba(0,0,0,0.45)" }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Onboarding Tasks {selectedOnboardEmployee ? `for ${selectedOnboardEmployee}` : ""}</h5>
                <button type="button" className="btn-close" onClick={() => setShowOnboardModal(false)}></button>
              </div>

              <div className="modal-body">
                {['admin', 'hr'].includes(role) && (
                  <form onSubmit={createOnboardingTask} className="mb-3">
                    <div className="row g-2 align-items-end">
                      <div className="col-md-4">
                        <label className="form-label">Employee</label>
                        <select className="form-select" value={selectedOnboardEmployee || ""} onChange={(e) => setSelectedOnboardEmployee(e.target.value || null)} required>
                          <option value="">-- select employee --</option>
                          {employees.map((emp) => (
                            <option key={emp.id} value={emp.id}>{emp.employee_id} — {emp.user?.first_name} {emp.user?.last_name}</option>
                          ))}
                        </select>
                      </div>

                      <div className="col-md-4">
                        <label className="form-label">Task Name</label>
                        <input className="form-control" name="task_name" value={onboardForm.task_name} onChange={handleOnboardChange} required />
                      </div>

                      <div className="col-md-2">
                        <label className="form-label">Due Date</label>
                        <input type="date" name="due_date" className="form-control" value={onboardForm.due_date} onChange={handleOnboardChange} required />
                      </div>

                      <div className="col-md-2">
                        <label className="form-label">Assigned To (user)</label>
                        <select className="form-select" name="assigned_to" value={onboardForm.assigned_to || ""} onChange={handleOnboardChange}>
                          <option value="">-- optional --</option>
                          {employees.filter((emp) => emp.user && emp.user.id).map((emp) => (
                            <option key={emp.user.id} value={emp.user.id}>{emp.user.email || `${emp.user.first_name} ${emp.user.last_name}`} ({emp.employee_id})</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="row g-2 mt-2">
                      <div className="col-md-8">
                        <label className="form-label">Task description</label>
                        <textarea name="task_description" className="form-control" placeholder="Task description (optional)" value={onboardForm.task_description} onChange={handleOnboardChange}></textarea>
                      </div>

                      <div className="col-md-3">
                        <label className="form-label">Notes (optional)</label>
                        <input name="notes" className="form-control" value={onboardForm.notes} onChange={handleOnboardChange} />
                      </div>

                      <div className="col-md-1 text-end">
                        <div className="d-grid">
                          <button className="btn btn-primary" type="submit" disabled={loading}>Create</button>
                        </div>
                      </div>
                    </div>
                  </form>
                )}

                <div>
                  {onboardingTasks.length === 0 && <div className="text-muted">No tasks found.</div>}
                  {onboardingTasks.map((t) => (
                    <div key={t.id} className="card mb-2">
                      <div className="card-body d-flex justify-content-between align-items-start">
                        <div>
                          <div className="fw-semibold">{t.task_name}</div>
                          <div className="small text-muted">{t.task_description}</div>
                          <div className="small text-muted">Status: {t.status} — Due: {t.due_date || "-"}</div>
                          <div className="small text-muted">Assigned to: {assignedToLabel(t)}</div>
                        </div>

                        <div className="text-end">
                          <div className="btn-group mb-2">
                            <button className="btn btn-sm btn-outline-primary" onClick={() => getOnboardingTaskDetail(t.id)}>View</button>
                            {(role === "admin" || role === "hr" || assignedToMatchesCurrentUser(t)) && (<button className="btn btn-sm btn-outline-success" onClick={() => completeOnboardingTask(t.id)}>Complete</button>)}
                            {['admin', 'hr'].includes(role) && (<button className="btn btn-sm btn-outline-danger" onClick={() => deleteOnboardingTask(t.id)}>Delete</button>)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setShowOnboardModal(false)}>Close</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showTaskDetailModal && taskDetail && (
        <div className="modal show d-block" tabIndex="-1" {...modalBackdropProps} style={{ background: "rgba(0,0,0,0.45)" }}>
          <div className="modal-dialog modal-lg">
            <form className="modal-content" onSubmit={async (e) => { e.preventDefault(); await updateOnboardingTask(taskDetail.id, taskEditForm); }}>
              <div className="modal-header">
                <h5 className="modal-title">Task: {taskDetail.task_name}</h5>
                <button type="button" className="btn-close" onClick={() => setShowTaskDetailModal(false)}></button>
              </div>

              <div className="modal-body">
                <div className="mb-2">
                  <label className="form-label">Task Name</label>
                  <input name="task_name" className="form-control" value={taskEditForm.task_name || ""} onChange={handleTaskEditChange} />
                </div>

                <div className="mb-2">
                  <label className="form-label">Description</label>
                  <textarea name="task_description" className="form-control" value={taskEditForm.task_description || ""} onChange={handleTaskEditChange}></textarea>
                </div>

                <div className="row g-2">
                  <div className="col-md-6">
                    <label className="form-label">Due Date</label>
                    <input type="date" name="due_date" className="form-control" value={taskEditForm.due_date || ""} onChange={handleTaskEditChange} />
                  </div>

                  <div className="col-md-6">
                    <label className="form-label">Status</label>
                    <select name="status" className="form-select" value={taskEditForm.status || ""} onChange={handleTaskEditChange}>
                      <option value="">-- select --</option>
                      <option value="PENDING">PENDING</option>
                      <option value="IN_PROGRESS">IN_PROGRESS</option>
                      <option value="COMPLETED">COMPLETED</option>
                      <option value="SKIPPED">SKIPPED</option>
                    </select>
                  </div>
                </div>

                <div className="mb-2">
                  <label className="form-label">Notes</label>
                  <textarea name="notes" className="form-control" value={taskEditForm.notes || ""} onChange={handleTaskEditChange}></textarea>
                </div>
              </div>

              <div className="modal-footer">
                {['admin', 'hr'].includes(role) && (<button type="button" className="btn btn-danger me-auto" onClick={() => deleteOnboardingTask(taskDetail.id)}>Delete</button>)}
                <button type="button" className="btn btn-secondary" onClick={() => setShowTaskDetailModal(false)}>Close</button>
                <button type="submit" className="btn btn-primary">Save (PATCH)</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showEmploymentModal && (
        <div className="modal show d-block" tabIndex="-1" {...modalBackdropProps} style={{ background: "rgba(0,0,0,0.45)" }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Employment History {selectedEmploymentEmployee ? `for ${selectedEmploymentEmployee}` : ""}</h5>
                <button type="button" className="btn-close" onClick={() => setShowEmploymentModal(false)}></button>
              </div>

              <div className="modal-body">
                <form onSubmit={handleEmploymentSave} className="mb-3">
                  <div className="row g-2">
                    <div className="col-md-4">
                      <label className="form-label">Company</label>
                      <input name="company_name" className="form-control" value={employmentForm.company_name} onChange={handleEmploymentChange} required />
                    </div>

                    <div className="col-md-4">
                      <label className="form-label">Designation</label>
                      <input name="designation" className="form-control" value={employmentForm.designation} onChange={handleEmploymentChange} />
                    </div>

                    <div className="col-md-2">
                      <label className="form-label">Start</label>
                      <input type="date" name="start_date" className="form-control" value={employmentForm.start_date} onChange={handleEmploymentChange} required />
                    </div>
                  </div>

                  <div className="row g-2 mt-2">
                    <div className="col-md-8">
                      <label className="form-label">Job Description</label>
                      <textarea name="job_description" className="form-control" value={employmentForm.job_description} onChange={handleEmploymentChange}></textarea>
                    </div>

                    <div className="col-md-4 d-flex flex-column">
                      <div className="mt-auto">
                        <button className="btn btn-primary me-2" type="submit" disabled={loading}>{editingEmploymentId ? "Update" : "Add"}</button>
                        {editingEmploymentId && (<button className="btn btn-secondary" type="button" onClick={() => { setEditingEmploymentId(null); setEmploymentForm({ company_name: "", designation: "", start_date: "", end_date: "", is_current: false, job_description: "" }); }}>Cancel</button>)}
                      </div>

                      <div className="form-check mb-2 mt-3">
                        <input className="form-check-input" type="checkbox" id="is_current" checked={employmentForm.is_current} onChange={handleEmploymentChange} name="is_current" />
                        <label className="form-check-label" htmlFor="is_current">Is Current</label>
                      </div>
                    </div>
                  </div>
                </form>

                <div>
                  {employmentRecords.length === 0 && <div className="text-muted">No employment records found.</div>}
                  {employmentRecords.map((rec) => (
                    <div key={rec.id} className="card mb-2">
                      <div className="card-body d-flex justify-content-between align-items-start">
                        <div>
                          <div className="fw-semibold">{rec.company_name} — {rec.designation}</div>
                          <div className="small text-muted">{rec.start_date} to {rec.end_date || (rec.is_current ? "Present" : "-")}</div>
                          <div className="small">{rec.job_description}</div>
                        </div>

                        <div className="text-end">
                          <div className="btn-group">
                            <button className="btn btn-sm btn-outline-primary" onClick={() => startEditEmployment(rec)}>Edit</button>
                            <button className="btn btn-sm btn-outline-danger" onClick={() => deleteEmploymentRecord(rec.id)}>Delete</button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="modal-footer">
                <button className="btn btn-secondary" onClick={() => setShowEmploymentModal(false)}>Close</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
