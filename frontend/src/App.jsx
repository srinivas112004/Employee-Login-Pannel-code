import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import Header from './components/Header';
import Footer from './components/Footer';
import ChatPage from "./pages/ChatPage";

import Home from './pages/Home';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Profile from './pages/Profile';
import ChangePassword from './pages/ChangePassword';
import UserList from './pages/UserList';

// Day 2 Components
import EmailVerification from './components/EmailVerification';
import PasswordReset from './components/PasswordReset';
import TwoFASetup from "./components/TwoFASetup";

// Day 6 Project Management
import ProjectManagement from './pages/ProjectManagement';

// Day 8 Leave Management pages
import LeaveDashboard from './pages/LeaveDashboard';
import LeaveHistory from './pages/LeaveHistory';
import ManagerApprovalPanel from './components/ManagerApprovalPanel';

// Day 20 LMS
import LMSPanel from './pages/LMSPanel';

// Day 22 Activity Logs & Audit Trail
import LogsPanel from './pages/LogsPanel';

// Day 23 Compliance & Policy Management
import CompliancePanel from './pages/CompliancePanel';

// Day 24 Document Management System
import DocumentsPanel from './pages/DocumentsPanel';





/**
 * Protected: checks authentication and loading state.
 */
function Protected({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return <div className="p-4">Loading...</div>;
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

/**
 * RoleProtected: checks that user is authenticated (via Protected)
 * and also that user's role is one of the allowed roles.
 */
function RoleProtected({ children, allowed = [] }) {
  const { user, loading } = useAuth();

  if (loading) return <div className="p-4">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;

  const role = (user.role || '').toLowerCase();

  if (!allowed || allowed.length === 0) return children;
  if (allowed.map(r => r.toLowerCase()).includes(role)) return children;

  return (
    <div className="container mt-4">
      <div className="alert alert-danger">
        Access Denied — you do not have permission to view this page.
      </div>
    </div>
  );
}

export default function App() {
  const { user } = useAuth();

  return (
    <div className="d-flex flex-column min-vh-100">
      <Header />

      <main className="flex-grow-1">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <Home />} />
          <Route path="/home" element={user ? <Navigate to="/dashboard" replace /> : <Home />} />
          <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login />} />

          {/* Employee dashboard */}
          <Route
            path="/employee/dashboard"
            element={
              <Protected>
                <ChatPage />
              </Protected>
            }
          />

          {/* Day 2 Routes */}
          <Route path="/verify-email" element={<Protected><EmailVerification /></Protected>} />
          <Route path="/password-reset" element={<PasswordReset />} />
          <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
          <Route path="/profile" element={<Protected><Profile /></Protected>} />
          <Route path="/change-password" element={<Protected><ChangePassword /></Protected>} />
          <Route
            path="/twofa-setup"
            element={
              <Protected>
                <TwoFASetup />
              </Protected>
            }
          />

          {/* Chat */}
          <Route
            path="/chat"
            element={
              <Protected>
                <ChatPage />
              </Protected>
            }
          />

          {/* Project Management */}
          <Route
            path="/projects"
            element={
              <Protected>
                <ProjectManagement />
              </Protected>
            }
          />
          <Route
            path="/projects/:id"
            element={
              <Protected>
                <ProjectManagement />
              </Protected>
            }
          />

          {/* Users */}
          <Route
            path="/users"
            element={
              <Protected>
                <RoleProtected allowed={['admin', 'hr', 'manager']}>
                  <UserList />
                </RoleProtected>
              </Protected>
            }
          />

          {/* Leave Management */}
          <Route
            path="/leaves"
            element={
              <Protected>
                <LeaveDashboard />
              </Protected>
            }
          />
          <Route
            path="/leaves/history"
            element={
              <Protected>
                <LeaveHistory />
              </Protected>
            }
          />
          <Route
            path="/leaves/pending"
            element={
              <Protected>
                <RoleProtected allowed={['manager']}>
                  <ManagerApprovalPanel />
                </RoleProtected>
              </Protected>
            }
          />

          {/* Day 16 Payroll Routes */}
          
          {/* Day 20 LMS */}
          <Route
            path="/lms"
            element={
              <Protected>
                <LMSPanel />
              </Protected>
            }
          />

          {/* Day 22 Activity Logs & Audit Trail */}
          <Route
            path="/logs"
            element={
              <Protected>
                <RoleProtected allowed={['admin', 'hr']}>
                  <LogsPanel />
                </RoleProtected>
              </Protected>
            }
          />

          {/* Day 23 Compliance & Policy Management */}
          <Route
            path="/compliance"
            element={
              <Protected>
                <CompliancePanel />
              </Protected>
            }
          />

          {/* Day 24 Document Management System */}
          <Route
            path="/documents"
            element={
              <Protected>
                <DocumentsPanel />
              </Protected>
            }
          />

          {/* Day 24 Document Management */}
          <Route
            path="/documents"
            element={
              <Protected>
                <DocumentsPanel />
              </Protected>
            }
          />
        
          {/* Fallback */}
          <Route path="*" element={<Navigate to={user ? "/dashboard" : "/"} replace />} />
        </Routes>
      </main>

      <Footer />
    </div>
  );
}
