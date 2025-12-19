// src/pages/Dashboard.jsx
import React, { useEffect, useState, lazy, Suspense } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import TasksPage from "./TasksPage";
import AnnouncementsPage from "./AnnouncementsPage";
import LeaveDashboard from "./LeaveDashboard";
import AttendancePage from "./AttendancePage";
import ChatPage from "./ChatPage";
import DeviceSessionManagement from "../components/DeviceSessionManager";
import HROverview from "./HROverview";

// Lazy-load panels
const PayrollPanel = lazy(() => import("./PayrollPanel"));
const ExpensesPanel = lazy(() => import("./ExpensesPanel"));
const PerformancePanel = lazy(() => import("./PerformancePanel"));
const ReviewsPanel = lazy(() => import("./ReviewsPanel"));
const LMSPanel = lazy(() => import("./LMSPanel")); // added LMSPanel
const CompliancePanel = lazy(() => import("./CompliancePanel")); // Day 23
const DocumentsPanel = lazy(() => import("./DocumentsPanel")); // Day 24

export default function Dashboard() {
  const { getProfile } = useAuth();
  const navigate = useNavigate();

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem("access_token");
  const BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";
  const [activeTab, setActiveTab] = useState("announcements");
  const [users, setUsers] = useState(null);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [latestAnnouncement, setLatestAnnouncement] = useState(null);
  const [loadingAnnouncement, setLoadingAnnouncement] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const p = await getProfile();
        setProfile(p || null);
        await loadUsers();
        await loadLatestAnnouncement();
      } catch (err) {
        console.error("Failed to load dashboard", err);
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadUsers = async () => {
    setLoadingUsers(true);
    try {
      const res = await fetch(`${BASE}/api/auth/users/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch users");
      const data = await res.json();
      const arr = Array.isArray(data) ? data : data?.results ?? [];
      const normalized = arr.map((u) => ({
        id: u.id ?? u.pk,
        display:
          u.full_name ||
          u.email ||
          u.username ||
          `${(u.first_name || "").trim()} ${(u.last_name || "").trim()}`.trim() ||
          String(u.id),
      }));
      setUsers(normalized);
    } catch {
      setUsers(null);
    }
    setLoadingUsers(false);
  };

  const loadLatestAnnouncement = async () => {
    setLoadingAnnouncement(true);
    try {
      const res = await fetch(`${BASE}/api/dashboard/announcements/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch announcements");
      const data = await res.json();
      const arr = Array.isArray(data) ? data : data?.results ?? [];
      if (arr.length) setLatestAnnouncement(arr[0]);
      else setLatestAnnouncement(null);
    } catch {
      setLatestAnnouncement(null);
    } finally {
      setLoadingAnnouncement(false);
    }
  };

  if (loading) return <div className="text-center mt-5">Loading dashboard...</div>;
  if (!profile) return <div className="text-center mt-5">No profile found.</div>;

  const role = (profile?.role || "").toLowerCase();

  return (
    <div className="container-fluid">
      <div className="row" style={{ minHeight: "85vh" }}>
        {/* Sidebar */}
        <aside className="col-12 col-md-3 col-lg-2 p-3 border-end" style={{ background: "#f8f9fa", minHeight: "100%" }}>
          <div className="row ps-3 mb-3">
            <div className="col-1 bi bi-person-fill text-primary h1"></div>
            <div
              className="col-9 ps-4 text-center"
              onClick={() => navigate("/profile")}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") navigate("/profile"); }}
              style={{ cursor: "pointer" }}
              title="Open profile"
            >
              <h5 className="fw-bold mb-0 text-primary">Profile</h5>
              <small className="text-muted">{profile?.full_name || profile?.first_name || "User"}</small>
            </div>
          </div>

          <div className="list-group list-group-flush">
            <SidebarButton id="overview" label="Overview" icon="🏠" activeTab={activeTab} setActiveTab={setActiveTab} />
            <SidebarButton id="announcements" label="Announcements" icon="📣" activeTab={activeTab} setActiveTab={setActiveTab} />
            <SidebarButton id="tasks" label="Tasks" icon="🗂️" activeTab={activeTab} setActiveTab={setActiveTab} />
            <SidebarButton id="attendance" label="Attendance" icon="⏱️" activeTab={activeTab} setActiveTab={setActiveTab} />
            <SidebarButton id="leave" label="Leave" icon="🗓️" activeTab={activeTab} setActiveTab={setActiveTab} />
            <SidebarButton id="chat" label="Chat" icon="💬" activeTab={activeTab} setActiveTab={setActiveTab} />
            <SidebarButton id="hr" label="HR" icon="🧾" activeTab={activeTab} setActiveTab={setActiveTab} />
            <SidebarButton id="performance" label="Performance & Reviews" icon="🎯" activeTab={activeTab} setActiveTab={setActiveTab} />
            <SidebarButton id="expenses" label="Expenses" icon="💼" activeTab={activeTab} setActiveTab={setActiveTab} />
            <SidebarButton id="lms" label="LMS" icon="📚" activeTab={activeTab} setActiveTab={setActiveTab} />
            <SidebarButton id="documents" label="Documents" icon="📄" activeTab={activeTab} setActiveTab={setActiveTab} />

            {role === "employee" && <SidebarButton id="payroll" label="My Payroll" icon="💸" activeTab={activeTab} setActiveTab={setActiveTab} />}
            {(role === "hr" || role === "admin" || role === "manager") && <SidebarButton id="payroll" label="Manage Payroll" icon="💸" activeTab={activeTab} setActiveTab={setActiveTab} />}
          </div>
        </aside>

        {/* Main Content */}
        <main className="col-12 col-md-9 col-lg-10 p-4 bg-white">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h2 className="text-primary fw-bold">
              {activeTab === "overview" && `Welcome, ${profile?.full_name || profile?.first_name || "User"}`}
              {activeTab === "announcements" && "Announcements"}
              {activeTab === "tasks" && "Tasks"}
              {activeTab === "attendance" && "Attendance"}
              {activeTab === "leave" && "Leave Dashboard"}
              {activeTab === "chat" && "Chat"}
              {activeTab === "hr" && "HR Overview"}
              {activeTab === "performance" && "Performance & Reviews"}
              {activeTab === "payroll" && "Payroll"}
              {activeTab === "expenses" && "Expenses & Reimbursements"}
              {activeTab === "lms" && "Learning Management System"}
              {activeTab === "documents" && "Document Management"}
            </h2>
          </div>

          {/* Tab Contents */}
          {activeTab === "overview" && (
            <div>
              {loadingAnnouncement ? (
                <div>Loading latest announcement...</div>
              ) : latestAnnouncement ? (
                <div className="card p-4 shadow-sm mb-4">
                  <h5>{latestAnnouncement.title}</h5>
                  <p>{latestAnnouncement.content}</p>
                  <small className="text-muted">{latestAnnouncement.created_at}</small>
                </div>
              ) : (
                <div>No announcements yet.</div>
              )}
              <DeviceSessionManagement BASE={BASE} token={token} />
            </div>
          )}

          {activeTab === "announcements" && <AnnouncementsPage BASE={BASE} token={token} profile={profile} />}
          {activeTab === "tasks" && <TasksPage BASE={BASE} token={token} profile={profile} users={users} loadingUsers={loadingUsers} />}
          {activeTab === "attendance" && <AttendancePage />}
          {activeTab === "leave" && <LeaveDashboard />}
          {activeTab === "chat" && <ChatPage BASE={BASE} token={token} profile={profile} users={users} loadingUsers={loadingUsers} />}
          {activeTab === "hr" && <HROverview />}

          {/* Lazy-loaded Panels */}
          {activeTab === "performance" && (
            <Suspense fallback={<div className="text-center py-6">Loading...</div>}>
              <div>
                <ul className="nav nav-tabs mb-3">
                  <li className="nav-item">
                    <button 
                      className="nav-link active" 
                      data-bs-toggle="tab" 
                      data-bs-target="#performance-tab"
                      type="button"
                    >
                      Performance Goals
                    </button>
                  </li>
                  <li className="nav-item">
                    <button 
                      className="nav-link" 
                      data-bs-toggle="tab" 
                      data-bs-target="#reviews-tab"
                      type="button"
                    >
                      Reviews
                    </button>
                  </li>
                </ul>
                <div className="tab-content">
                  <div className="tab-pane fade show active" id="performance-tab">
                    <PerformancePanel />
                  </div>
                  <div className="tab-pane fade" id="reviews-tab">
                    <ReviewsPanel />
                  </div>
                </div>
              </div>
            </Suspense>
          )}
          {activeTab === "expenses" && (
            <Suspense fallback={<div className="text-center py-6">Loading expenses...</div>}>
              <ExpensesPanel />
            </Suspense>
          )}
          {activeTab === "payroll" && (
            <Suspense fallback={<div className="text-center py-6">Loading payroll...</div>}>
              <PayrollPanel />
            </Suspense>
          )}
          {activeTab === "lms" && (
            <Suspense fallback={<div className="text-center py-6">Loading LMS...</div>}>
              <LMSPanel />
            </Suspense>
          )}
          {activeTab === "documents" && (
            <Suspense fallback={<div className="text-center py-6">Loading Documents...</div>}>
              <DocumentsPanel />
            </Suspense>
          )}
        </main>
      </div>
    </div>
  );
}

function SidebarButton({ id, label, icon, activeTab, setActiveTab }) {
  const isActive = activeTab === id;
  return (
    <button
      className={`list-group-item list-group-item-action mb-2 text-start fw-semibold border-0 ${isActive ? "active" : ""}`}
      style={{
        borderRadius: "10px",
        backgroundColor: isActive ? "#0d6efd" : "#ffffff",
        color: isActive ? "#ffffff" : "#333",
        boxShadow: isActive ? "0 2px 6px rgba(13,110,253,0.3)" : "0 1px 3px rgba(0,0,0,0.05)",
        transition: "all 0.3s ease",
      }}
      onClick={() => setActiveTab(id)}
      type="button"
      onMouseEnter={(e) => { if (!isActive) e.currentTarget.style.backgroundColor = "#f1f3f5"; }}
      onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.backgroundColor = "#ffffff"; }}
    >
      <span style={{ fontSize: "1.1rem" }}>{icon}</span>
      <span className="ms-2">{label}</span>
    </button>
  );
}
