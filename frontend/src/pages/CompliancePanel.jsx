import React, { useState, useEffect } from "react";
import { Table, Button, Badge, Modal, Form, Alert, Tabs, Tab, ProgressBar } from "react-bootstrap";
import { useAuth } from "../context/AuthContext";

const API_BASE = "http://localhost:8000/api/compliance";

/* ================= AUTH HEADERS ================= */
const authHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  "Content-Type": "application/json",
});

export default function CompliancePanel() {
  /* ================= AUTH & ROLE ================= */
  const { user } = useAuth();
  const role = (user?.role || "").toLowerCase();
  const isAdminOrHR = role === "admin" || role === "hr";

  // State for Categories
  const [categories, setCategories] = useState([]);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [categoryForm, setCategoryForm] = useState({ id: null, name: "", description: "" });
  
  // State for Policies
  const [policies, setPolicies] = useState([]);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [showPolicyDetail, setShowPolicyDetail] = useState(false);
  const [policyForm, setPolicyForm] = useState({
    id: null,
    title: "",
    category: "",
    content: "",
    version: "1.0",
    effective_date: "",
    mandatory: false,
    applies_to_roles: []
  });

  // State for Pending Acknowledgments
  const [pendingPolicies, setPendingPolicies] = useState([]);
  
  // State for Acknowledgments (Admin view)
  const [acknowledgments, setAcknowledgments] = useState([]);
  const [ackFilters, setAckFilters] = useState({ policy: "", user: "" });
  
  // State for Compliance Reports
  const [myCompliance, setMyCompliance] = useState(null);
  const [complianceReport, setComplianceReport] = useState(null);
  
  // State for Signature Modal
  const [showSignatureModal, setShowSignatureModal] = useState(false);
  const [policyToAcknowledge, setPolicyToAcknowledge] = useState(null);
  const [signatureForm, setSignatureForm] = useState({ signature: "", comments: "" });
  
  // UI State
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [activeTab, setActiveTab] = useState("policies");

  useEffect(() => {
    loadCategories();
    loadPolicies();
    loadPendingPolicies();
    loadMyCompliance();
    if (isAdminOrHR) {
      loadAcknowledgments();
      loadComplianceReport();
    }
  }, [isAdminOrHR]);

  // ================= POLICY CATEGORIES (APIs 1-5) =================
  
  // API #1: List categories
  const loadCategories = async () => {
    try {
      const res = await fetch(`${API_BASE}/categories/`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load categories');
      const data = await res.json();
      setCategories(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError(err.message);
    }
  };

  // API #2 & #4: Create/Update category
  const saveCategory = async () => {
    try {
      const method = categoryForm.id ? 'PUT' : 'POST';
      const url = categoryForm.id 
        ? `${API_BASE}/categories/${categoryForm.id}/`
        : `${API_BASE}/categories/`;
      
      const res = await fetch(url, {
        method,
        headers: authHeaders(),
        body: JSON.stringify({
          name: categoryForm.name,
          description: categoryForm.description
        })
      });
      
      if (!res.ok) throw new Error('Failed to save category');
      
      setSuccess(categoryForm.id ? 'Category updated' : 'Category created');
      setShowCategoryModal(false);
      setCategoryForm({ id: null, name: "", description: "" });
      loadCategories();
    } catch (err) {
      setError(err.message);
    }
  };

  // API #5: Delete category
  const deleteCategory = async (id) => {
    if (!window.confirm('Delete this category?')) return;
    try {
      const res = await fetch(`${API_BASE}/categories/${id}/`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to delete category');
      setSuccess('Category deleted');
      loadCategories();
    } catch (err) {
      setError(err.message);
    }
  };

  // ================= POLICY MANAGEMENT (APIs 6-10) =================
  
  // API #6: List policies
  const loadPolicies = async () => {
    try {
      const res = await fetch(`${API_BASE}/policies/`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load policies');
      const data = await res.json();
      setPolicies(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError(err.message);
    }
  };

  // API #7 & #9: Create/Update policy
  const savePolicy = async () => {
    try {
      const method = policyForm.id ? 'PUT' : 'POST';
      const url = policyForm.id 
        ? `${API_BASE}/policies/${policyForm.id}/`
        : `${API_BASE}/policies/`;
      
      const res = await fetch(url, {
        method,
        headers: authHeaders(),
        body: JSON.stringify({
          title: policyForm.title,
          category: policyForm.category,
          content: policyForm.content,
          version: policyForm.version,
          effective_date: policyForm.effective_date,
          is_mandatory: policyForm.mandatory,
          applies_to_roles: policyForm.applies_to_roles
        })
      });
      
      if (!res.ok) throw new Error('Failed to save policy');
      
      setSuccess(policyForm.id ? 'Policy updated' : 'Policy created');
      setShowPolicyModal(false);
      resetPolicyForm();
      loadPolicies();
    } catch (err) {
      setError(err.message);
    }
  };

  // API #8: Get policy details
  const viewPolicyDetails = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/policies/${id}/`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load policy details');
      const data = await res.json();
      setSelectedPolicy(data);
      setShowPolicyDetail(true);
    } catch (err) {
      setError(err.message);
    }
  };

  // API #10: Delete policy
  const deletePolicy = async (id) => {
    if (!window.confirm('Delete this policy?')) return;
    try {
      const res = await fetch(`${API_BASE}/policies/${id}/`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to delete policy');
      setSuccess('Policy deleted');
      loadPolicies();
    } catch (err) {
      setError(err.message);
    }
  };

  // ================= POLICY LIFECYCLE (APIs 11-12) =================
  
  // API #11: Publish policy
  const publishPolicy = async (id) => {
    if (!window.confirm('Publish this policy?')) return;
    try {
      const res = await fetch(`${API_BASE}/policies/${id}/publish/`, {
        method: 'POST',
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to publish policy');
      setSuccess('Policy published');
      loadPolicies();
    } catch (err) {
      setError(err.message);
    }
  };

  // API #12: Archive policy
  const archivePolicy = async (id) => {
    if (!window.confirm('Archive this policy?')) return;
    try {
      const res = await fetch(`${API_BASE}/policies/${id}/archive/`, {
        method: 'POST',
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to archive policy');
      setSuccess('Policy archived');
      loadPolicies();
    } catch (err) {
      setError(err.message);
    }
  };

  // ================= ACKNOWLEDGMENTS (APIs 13-17) =================
  
  // API #13: Get pending policies
  const loadPendingPolicies = async () => {
    try {
      const res = await fetch(`${API_BASE}/policies/pending/`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load pending policies');
      const data = await res.json();
      setPendingPolicies(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError(err.message);
    }
  };

  // API #14: Acknowledge policy (check if signature is needed first)
  const initiateAcknowledgment = async (policy) => {
    if (policy.requires_signature) {
      // Show signature modal
      setPolicyToAcknowledge(policy);
      setSignatureForm({ signature: "", comments: "" });
      setShowSignatureModal(true);
    } else {
      // Acknowledge directly without signature
      await submitAcknowledgment(policy.id, {});
    }
  };

  // Submit acknowledgment with optional signature
  const submitAcknowledgment = async (policyId, data = {}) => {
    try {
      const res = await fetch(`${API_BASE}/policies/${policyId}/acknowledge/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(data)
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        const errorMsg = errorData.detail || errorData.error || errorData.message || 
                        JSON.stringify(errorData) || 'Failed to acknowledge policy';
        throw new Error(errorMsg);
      }
      setSuccess('Policy acknowledged successfully');
      setShowSignatureModal(false);
      setPolicyToAcknowledge(null);
      loadPendingPolicies();
      loadMyCompliance();
    } catch (err) {
      setError(err.message);
    }
  };

  // Handle signature form submission
  const handleSignatureSubmit = () => {
    if (policyToAcknowledge && policyToAcknowledge.requires_signature && !signatureForm.signature.trim()) {
      setError('Signature is required for this policy');
      return;
    }
    submitAcknowledgment(policyToAcknowledge.id, signatureForm);
  };

  // API #15-17: List acknowledgments with filters
  const loadAcknowledgments = async () => {
    try {
      const params = new URLSearchParams();
      if (ackFilters.policy) params.append('policy', ackFilters.policy);
      if (ackFilters.user) params.append('user', ackFilters.user);
      
      const res = await fetch(`${API_BASE}/acknowledgments/?${params}`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load acknowledgments');
      const data = await res.json();
      setAcknowledgments(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError(err.message);
    }
  };

  // ================= COMPLIANCE REPORTS (APIs 18-19) =================
  
  // API #18: My compliance status
  const loadMyCompliance = async () => {
    try {
      const res = await fetch(`${API_BASE}/policies/my_compliance/`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load compliance status');
      const data = await res.json();
      setMyCompliance(data);
    } catch (err) {
      setError(err.message);
    }
  };

  // API #19: Organization-wide report
  const loadComplianceReport = async () => {
    try {
      const res = await fetch(`${API_BASE}/policies/compliance_report/`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load compliance report');
      const data = await res.json();
      setComplianceReport(data);
    } catch (err) {
      setError(err.message);
    }
  };

  // ================= UTILITY FUNCTIONS =================
  
  const resetPolicyForm = () => {
    setPolicyForm({
      id: null,
      title: "",
      category: "",
      content: "",
      version: "1.0",
      effective_date: "",
      mandatory: false,
      applies_to_roles: []
    });
  };

  const openEditPolicy = (policy) => {
    setPolicyForm({
      id: policy.id,
      title: policy.title,
      category: policy.category,
      content: policy.content,
      version: policy.version,
      effective_date: policy.effective_date,
      mandatory: policy.is_mandatory || policy.mandatory,
      applies_to_roles: policy.applies_to_roles || []
    });
    setShowPolicyModal(true);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'published': return 'success';
      case 'draft': return 'secondary';
      case 'archived': return 'warning';
      default: return 'info';
    }
  };

  // ================= RENDER =================

  return (
    <div className="container-fluid mt-4">
      <h3>Compliance & Policy Management</h3>
      
      {error && (
        <Alert variant="danger" onClose={() => setError("")} dismissible>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert variant="success" onClose={() => setSuccess("")} dismissible>
          {success}
        </Alert>
      )}

      <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k)} className="mb-3">
        
        {/* ========== POLICIES TAB ========== */}
        <Tab eventKey="policies" title="Policies">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5>Company Policies</h5>
            {isAdminOrHR && (
              <Button variant="primary" onClick={() => {
                resetPolicyForm();
                setShowPolicyModal(true);
              }}>
                + Create Policy
              </Button>
            )}
          </div>

          <Table bordered hover size="sm" responsive>
            <thead>
              <tr>
                <th>Title</th>
                <th>Category</th>
                <th>Version</th>
                <th>Status</th>
                <th>Effective Date</th>
                <th>Mandatory</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {policies.length === 0 && (
                <tr>
                  <td colSpan="7" className="text-center">No policies found</td>
                </tr>
              )}
              {policies.map((policy) => (
                <tr key={policy.id}>
                  <td>{policy.title}</td>
                  <td>{policy.category_name || policy.category}</td>
                  <td>{policy.version}</td>
                  <td>
                    <Badge bg={getStatusBadge(policy.status)}>{policy.status}</Badge>
                  </td>
                  <td>{policy.effective_date}</td>
                  <td>{policy.mandatory ? '✓' : '-'}</td>
                  <td>
                    <Button size="sm" variant="outline-info" onClick={() => viewPolicyDetails(policy.id)} className="me-1">
                      View
                    </Button>
                    {isAdminOrHR && (
                      <>
                        <Button size="sm" variant="outline-primary" onClick={() => openEditPolicy(policy)} className="me-1">
                          Edit
                        </Button>
                        {policy.status === 'draft' && (
                          <Button size="sm" variant="success" onClick={() => publishPolicy(policy.id)} className="me-1">
                            Publish
                          </Button>
                        )}
                        {policy.status === 'published' && (
                          <Button size="sm" variant="warning" onClick={() => archivePolicy(policy.id)} className="me-1">
                            Archive
                          </Button>
                        )}
                        <Button size="sm" variant="outline-danger" onClick={() => deletePolicy(policy.id)}>
                          Delete
                        </Button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Tab>

        {/* ========== PENDING ACKNOWLEDGMENTS TAB ========== */}
        <Tab eventKey="pending" title={`Pending (${pendingPolicies.length})`}>
          <h5>Policies Requiring Your Acknowledgment</h5>
          
          {pendingPolicies.length === 0 ? (
            <Alert variant="success">All policies acknowledged! ✓</Alert>
          ) : (
            <div className="row">
              {pendingPolicies.map((policy) => (
                <div key={policy.id} className="col-md-6 mb-3">
                  <div className="card">
                    <div className="card-header d-flex justify-content-between align-items-center">
                      <strong>{policy.title}</strong>
                      <Badge bg="warning">Pending</Badge>
                    </div>
                    <div className="card-body">
                      <p className="mb-2"><strong>Version:</strong> {policy.version}</p>
                      <p className="mb-2"><strong>Effective:</strong> {policy.effective_date}</p>
                      <p className="mb-3">{policy.content?.substring(0, 150)}...</p>
                      <div className="d-flex gap-2">
                        <Button size="sm" variant="info" onClick={() => viewPolicyDetails(policy.id)}>
                          Read Full Policy
                        </Button>
                        <Button size="sm" variant="success" onClick={() => initiateAcknowledgment(policy)}>
                          Acknowledge
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Tab>

        {/* ========== MY COMPLIANCE TAB ========== */}
        <Tab eventKey="my-compliance" title="My Compliance">
          <h5>My Compliance Status</h5>
          
          {myCompliance && (
            <>
              <div className="row mb-4">
                <div className="col-md-3">
                  <div className="card text-center">
                    <div className="card-body">
                      <h2 className="text-primary">{myCompliance.total_policies}</h2>
                      <p className="text-muted mb-0">Total Policies</p>
                    </div>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="card text-center">
                    <div className="card-body">
                      <h2 className="text-success">{myCompliance.acknowledged_count}</h2>
                      <p className="text-muted mb-0">Acknowledged</p>
                    </div>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="card text-center">
                    <div className="card-body">
                      <h2 className="text-warning">{myCompliance.pending_count}</h2>
                      <p className="text-muted mb-0">Pending</p>
                    </div>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="card text-center">
                    <div className="card-body">
                      <h2 className="text-info">{myCompliance.compliance_percentage}%</h2>
                      <p className="text-muted mb-0">Compliance Rate</p>
                    </div>
                  </div>
                </div>
              </div>

              <ProgressBar 
                now={myCompliance.compliance_percentage} 
                label={`${myCompliance.compliance_percentage}%`}
                variant="success"
                className="mb-3"
              />

              {/* Show All Policies with Status */}
              <h6 className="mt-4">All Policies</h6>
              <Table bordered size="sm" responsive>
                <thead>
                  <tr>
                    <th>Policy</th>
                    <th>Version</th>
                    <th>Effective Date</th>
                    <th>Status</th>
                    <th>Acknowledged At</th>
                  </tr>
                </thead>
                <tbody>
                  {policies.filter(p => p.status === 'published').map((policy) => {
                    const isPending = myCompliance.pending_policies?.some(pp => pp.id === policy.id);
                    const ackStatus = policy.acknowledgment_status;
                    
                    return (
                      <tr key={policy.id}>
                        <td>{policy.title}</td>
                        <td>{policy.version}</td>
                        <td>{policy.effective_date}</td>
                        <td>
                          {ackStatus?.acknowledged ? (
                            <Badge bg="success">Acknowledged</Badge>
                          ) : (
                            <Badge bg="warning">Pending</Badge>
                          )}
                        </td>
                        <td>
                          {ackStatus?.acknowledged_at 
                            ? new Date(ackStatus.acknowledged_at).toLocaleString() 
                            : '-'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </Table>
            </>
          )}
        </Tab>

        {/* ========== CATEGORIES TAB (Admin/HR) ========== */}
        {isAdminOrHR && (
          <Tab eventKey="categories" title="Categories">
            <div className="d-flex justify-content-between align-items-center mb-3">
              <h5>Policy Categories</h5>
              <Button variant="primary" onClick={() => {
                setCategoryForm({ id: null, name: "", description: "" });
                setShowCategoryModal(true);
              }}>
                + Add Category
              </Button>
            </div>

            <Table bordered hover size="sm">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {categories.length === 0 && (
                  <tr>
                    <td colSpan="3" className="text-center">No categories</td>
                  </tr>
                )}
                {categories.map((cat) => (
                  <tr key={cat.id}>
                    <td>{cat.name}</td>
                    <td>{cat.description}</td>
                    <td>
                      <Button 
                        size="sm" 
                        variant="outline-primary" 
                        onClick={() => {
                          setCategoryForm({ id: cat.id, name: cat.name, description: cat.description });
                          setShowCategoryModal(true);
                        }}
                        className="me-1"
                      >
                        Edit
                      </Button>
                      <Button size="sm" variant="outline-danger" onClick={() => deleteCategory(cat.id)}>
                        Delete
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Tab>
        )}

        {/* ========== ACKNOWLEDGMENTS TAB (Admin/HR) ========== */}
        {isAdminOrHR && (
          <Tab eventKey="acknowledgments" title="Acknowledgments">
            <h5>All Acknowledgments</h5>
            
            <div className="card mb-3">
              <div className="card-body">
                <div className="row g-2">
                  <div className="col-md-4">
                    <Form.Control
                      size="sm"
                      placeholder="Policy ID"
                      value={ackFilters.policy}
                      onChange={(e) => setAckFilters({ ...ackFilters, policy: e.target.value })}
                    />
                  </div>
                  <div className="col-md-4">
                    <Form.Control
                      size="sm"
                      placeholder="User ID"
                      value={ackFilters.user}
                      onChange={(e) => setAckFilters({ ...ackFilters, user: e.target.value })}
                    />
                  </div>
                  <div className="col-md-2">
                    <Button size="sm" variant="primary" onClick={loadAcknowledgments} className="w-100">
                      Filter
                    </Button>
                  </div>
                  <div className="col-md-2">
                    <Button 
                      size="sm" 
                      variant="secondary" 
                      onClick={() => {
                        setAckFilters({ policy: "", user: "" });
                        setTimeout(loadAcknowledgments, 100);
                      }}
                      className="w-100"
                    >
                      Clear
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            <Table bordered hover size="sm" responsive>
              <thead>
                <tr>
                  <th>Policy</th>
                  <th>User</th>
                  <th>Acknowledged At</th>
                  <th>IP Address</th>
                </tr>
              </thead>
              <tbody>
                {acknowledgments.length === 0 && (
                  <tr>
                    <td colSpan="4" className="text-center">No acknowledgments</td>
                  </tr>
                )}
                {acknowledgments.map((ack) => (
                  <tr key={ack.id}>
                    <td>{ack.policy_title || ack.policy}</td>
                    <td>{ack.user_name || ack.user}</td>
                    <td>{new Date(ack.acknowledged_at).toLocaleString()}</td>
                    <td>{ack.ip_address || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </Tab>
        )}

        {/* ========== COMPLIANCE REPORT TAB (Admin/HR) ========== */}
        {isAdminOrHR && (
          <Tab eventKey="report" title="Compliance Report">
            <h5>Organization-Wide Compliance Report</h5>
            
            {complianceReport && complianceReport.length > 0 && (
              <>
                <div className="row mb-4">
                  <div className="col-md-3">
                    <div className="card text-center">
                      <div className="card-body">
                        <h2 className="text-primary">{complianceReport.length}</h2>
                        <p className="text-muted mb-0">Total Users</p>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-3">
                    <div className="card text-center">
                      <div className="card-body">
                        <h2 className="text-success">
                          {complianceReport.reduce((sum, u) => sum + u.acknowledged, 0)}
                        </h2>
                        <p className="text-muted mb-0">Total Acknowledgments</p>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-3">
                    <div className="card text-center">
                      <div className="card-body">
                        <h2 className="text-warning">
                          {complianceReport.reduce((sum, u) => sum + u.pending, 0)}
                        </h2>
                        <p className="text-muted mb-0">Total Pending</p>
                      </div>
                    </div>
                  </div>
                  <div className="col-md-3">
                    <div className="card text-center">
                      <div className="card-body">
                        <h2 className="text-info">
                          {(complianceReport.reduce((sum, u) => sum + u.compliance_percentage, 0) / complianceReport.length).toFixed(2)}%
                        </h2>
                        <p className="text-muted mb-0">Avg Compliance Rate</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="card">
                  <div className="card-header">
                    <strong>User Compliance Details</strong>
                  </div>
                  <div className="card-body">
                    <Table bordered hover size="sm" responsive>
                      <thead>
                        <tr>
                          <th>User</th>
                          <th>Role</th>
                          <th>Total</th>
                          <th>Acknowledged</th>
                          <th>Pending</th>
                          <th>Overdue</th>
                          <th>Compliance %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {complianceReport.map((user) => (
                          <tr key={user.user_id}>
                            <td>
                              <div>{user.user_name}</div>
                              <small className="text-muted">{user.user_email}</small>
                            </td>
                            <td>
                              <Badge bg="secondary">{user.role}</Badge>
                            </td>
                            <td>{user.total_policies}</td>
                            <td>
                              <Badge bg="success">{user.acknowledged}</Badge>
                            </td>
                            <td>
                              <Badge bg="warning">{user.pending}</Badge>
                            </td>
                            <td>
                              <Badge bg="danger">{user.overdue}</Badge>
                            </td>
                            <td>
                              <ProgressBar 
                                now={user.compliance_percentage} 
                                label={`${user.compliance_percentage}%`}
                                variant={user.compliance_percentage >= 80 ? 'success' : user.compliance_percentage >= 50 ? 'warning' : 'danger'}
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                </div>
              </>
            )}
          </Tab>
        )}
      </Tabs>

      {/* ========== CATEGORY MODAL ========== */}
      <Modal show={showCategoryModal} onHide={() => setShowCategoryModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>{categoryForm.id ? 'Edit' : 'Create'} Category</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Name *</Form.Label>
            <Form.Control
              value={categoryForm.name}
              onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
              placeholder="Category name"
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={categoryForm.description}
              onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
              placeholder="Description"
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCategoryModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={saveCategory}>
            Save
          </Button>
        </Modal.Footer>
      </Modal>

      {/* ========== POLICY MODAL ========== */}
      <Modal show={showPolicyModal} onHide={() => setShowPolicyModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>{policyForm.id ? 'Edit' : 'Create'} Policy</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Title *</Form.Label>
            <Form.Control
              value={policyForm.title}
              onChange={(e) => setPolicyForm({ ...policyForm, title: e.target.value })}
              placeholder="Policy title"
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Category *</Form.Label>
            <Form.Select
              value={policyForm.category}
              onChange={(e) => setPolicyForm({ ...policyForm, category: e.target.value })}
            >
              <option value="">Select category</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Content *</Form.Label>
            <Form.Control
              as="textarea"
              rows={6}
              value={policyForm.content}
              onChange={(e) => setPolicyForm({ ...policyForm, content: e.target.value })}
              placeholder="Policy content"
            />
          </Form.Group>
          <div className="row">
            <div className="col-md-6">
              <Form.Group className="mb-3">
                <Form.Label>Version</Form.Label>
                <Form.Control
                  value={policyForm.version}
                  onChange={(e) => setPolicyForm({ ...policyForm, version: e.target.value })}
                  placeholder="1.0"
                />
              </Form.Group>
            </div>
            <div className="col-md-6">
              <Form.Group className="mb-3">
                <Form.Label>Effective Date</Form.Label>
                <Form.Control
                  type="date"
                  value={policyForm.effective_date}
                  onChange={(e) => setPolicyForm({ ...policyForm, effective_date: e.target.value })}
                />
              </Form.Group>
            </div>
          </div>
          <Form.Group className="mb-3">
            <Form.Check
              type="checkbox"
              label="Mandatory for all employees"
              checked={policyForm.mandatory}
              onChange={(e) => setPolicyForm({ ...policyForm, mandatory: e.target.checked })}
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Target Roles (comma-separated, leave empty for all)</Form.Label>
            <Form.Control
              value={policyForm.applies_to_roles.join(', ')}
              onChange={(e) => setPolicyForm({ 
                ...policyForm, 
                applies_to_roles: e.target.value.split(',').map(r => r.trim()).filter(Boolean)
              })}
              placeholder="employee, manager, hr"
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowPolicyModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={savePolicy}>
            Save
          </Button>
        </Modal.Footer>
      </Modal>

      {/* ========== POLICY DETAIL MODAL ========== */}
      <Modal show={showPolicyDetail} onHide={() => setShowPolicyDetail(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Policy Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedPolicy && (
            <>
              <h4>{selectedPolicy.title}</h4>
              <p>
                <Badge bg={getStatusBadge(selectedPolicy.status)}>{selectedPolicy.status}</Badge>
                {selectedPolicy.mandatory && <Badge bg="danger" className="ms-2">Mandatory</Badge>}
              </p>
              <p><strong>Category:</strong> {selectedPolicy.category_name || selectedPolicy.category}</p>
              <p><strong>Version:</strong> {selectedPolicy.version}</p>
              <p><strong>Effective Date:</strong> {selectedPolicy.effective_date}</p>
              <p><strong>Created:</strong> {new Date(selectedPolicy.created_at).toLocaleString()}</p>
              <hr />
              <div style={{ whiteSpace: 'pre-wrap' }}>{selectedPolicy.content}</div>
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowPolicyDetail(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>

      {/* ========== SIGNATURE MODAL ========== */}
      <Modal show={showSignatureModal} onHide={() => setShowSignatureModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Acknowledge Policy</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {policyToAcknowledge && (
            <>
              <h5>{policyToAcknowledge.title}</h5>
              <p className="text-muted">Version: {policyToAcknowledge.version}</p>
              <hr />
              
              {policyToAcknowledge.requires_signature && (
                <Alert variant="info">
                  <i className="bi bi-pen me-2"></i>
                  This policy requires your signature to acknowledge.
                </Alert>
              )}

              <Form.Group className="mb-3">
                <Form.Label>
                  Signature {policyToAcknowledge.requires_signature && <span className="text-danger">*</span>}
                </Form.Label>
                <Form.Control
                  type="text"
                  value={signatureForm.signature}
                  onChange={(e) => setSignatureForm({ ...signatureForm, signature: e.target.value })}
                  placeholder="Type your full name to sign"
                  required={policyToAcknowledge.requires_signature}
                />
                <Form.Text className="text-muted">
                  By typing your name, you acknowledge that you have read and understood this policy.
                </Form.Text>
              </Form.Group>

              <Form.Group className="mb-3">
                <Form.Label>Comments (Optional)</Form.Label>
                <Form.Control
                  as="textarea"
                  rows={3}
                  value={signatureForm.comments}
                  onChange={(e) => setSignatureForm({ ...signatureForm, comments: e.target.value })}
                  placeholder="Any comments or questions about this policy..."
                />
              </Form.Group>
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowSignatureModal(false)}>
            Cancel
          </Button>
          <Button variant="success" onClick={handleSignatureSubmit}>
            <i className="bi bi-check-circle me-1"></i>
            Acknowledge Policy
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}
