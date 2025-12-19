import React, { useState, useEffect } from "react";
import { Table, Button, Badge, Modal, Form, Alert, ProgressBar, Tabs, Tab } from "react-bootstrap";
import { useAuth } from "../context/AuthContext";

const API_BASE = "http://localhost:8000/api/logs";

/* ================= AUTH HEADERS ================= */
const authHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  "Content-Type": "application/json",
});

function LogsPanel() {
  /* ================= AUTH & ROLE ================= */
  const { user } = useAuth();
  const role = (user?.role || "").toLowerCase();

  // State for Activity Logs
  const [activityLogs, setActivityLogs] = useState([]);
  const [logFilters, setLogFilters] = useState({
    page: 1,
    page_size: 25,
    action: '',
    method: '',
    model_name: '',
    status_code: '',
    user_id: '',
    start_date: '',
    end_date: ''
  });
  const [logPagination, setLogPagination] = useState({ total: 0, page: 1, pageSize: 25, totalPages: 1 });
  
  // State for Search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searchPagination, setSearchPagination] = useState({ total: 0, page: 1, pageSize: 25, totalPages: 1 });
  
  // State for Statistics
  const [stats, setStats] = useState(null);
  const [statsDays, setStatsDays] = useState(7);
  
  // State for Audit Trail
  const [auditTrail, setAuditTrail] = useState([]);
  const [auditFilters, setAuditFilters] = useState({
    page: 1,
    page_size: 25,
    model_name: '',
    action: ''
  });
  const [auditPagination, setAuditPagination] = useState({ total: 0, page: 1, pageSize: 25, totalPages: 1 });
  
  // State for Object History
  const [objectHistory, setObjectHistory] = useState(null);
  const [showObjectHistory, setShowObjectHistory] = useState(false);
  const [historyModel, setHistoryModel] = useState('');
  const [historyObjectId, setHistoryObjectId] = useState('');
  
  // State for Log Detail Modal
  const [selectedLog, setSelectedLog] = useState(null);
  const [showLogDetail, setShowLogDetail] = useState(false);
  
  // UI State
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("activity");

  // Check if user has access (Admin/HR only)
  const hasAccess = role === "admin" || role === "hr";

  useEffect(() => {
    if (hasAccess) {
      loadActivityLogs();
      loadStats();
    }
  }, [hasAccess]);

  // ================= ACTIVITY LOGS =================
  
  // API #1-4: List activity logs with filters
  const loadActivityLogs = async () => {
    try {
      const params = new URLSearchParams();
      Object.entries(logFilters).forEach(([key, value]) => {
        if (value !== '' && value !== null && value !== undefined) {
          params.append(key, value);
        }
      });
      
      const res = await fetch(`${API_BASE}/activity/?${params}`, {
        headers: authHeaders()
      });
      
      if (!res.ok) {
        throw new Error('Failed to load activity logs');
      }
      
      const data = await res.json();
      setActivityLogs(data.results || []);
      setLogPagination({
        total: data.count,
        page: data.page,
        pageSize: data.page_size,
        totalPages: data.total_pages
      });
    } catch (err) {
      setError(err.message);
    }
  };

  const applyFilters = () => {
    setLogFilters({ ...logFilters, page: 1 });
    setTimeout(loadActivityLogs, 100);
  };

  const clearFilters = () => {
    setLogFilters({
      page: 1,
      page_size: 25,
      action: '',
      method: '',
      model_name: '',
      status_code: '',
      user_id: '',
      start_date: '',
      end_date: ''
    });
    setTimeout(loadActivityLogs, 100);
  };

  const handlePageChange = (newPage) => {
    setLogFilters({ ...logFilters, page: newPage });
    setTimeout(loadActivityLogs, 100);
  };

  // View log detail
  const viewLogDetail = (log) => {
    setSelectedLog(log);
    setShowLogDetail(true);
  };

  // ================= SEARCH & ANALYTICS =================
  
  // API #5-6: Full-text search
  const performSearch = async (page = 1) => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    
    try {
      const params = new URLSearchParams({
        q: searchQuery,
        page: page,
        page_size: 25
      });
      
      const res = await fetch(`${API_BASE}/activity/search/?${params}`, {
        headers: authHeaders()
      });
      
      if (!res.ok) {
        throw new Error('Search failed');
      }
      
      const data = await res.json();
      setSearchResults(data.results || []);
      setSearchPagination({
        total: data.count,
        page: data.page,
        pageSize: data.page_size,
        totalPages: data.total_pages
      });
    } catch (err) {
      setError(err.message);
    }
  };

  // API #7: Usage stats for dashboard
  const loadStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/activity/stats/?days=${statsDays}`, {
        headers: authHeaders()
      });
      
      if (!res.ok) {
        throw new Error('Failed to load statistics');
      }
      
      const data = await res.json();
      setStats(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const changeStatsPeriod = (days) => {
    setStatsDays(days);
    setTimeout(() => loadStats(), 100);
  };

  // ================= AUDIT TRAIL =================
  
  // API #8-9: List audit records
  const loadAuditTrail = async () => {
    try {
      const params = new URLSearchParams();
      Object.entries(auditFilters).forEach(([key, value]) => {
        if (value !== '' && value !== null && value !== undefined) {
          params.append(key, value);
        }
      });
      
      const res = await fetch(`${API_BASE}/audit/?${params}`, {
        headers: authHeaders()
      });
      
      if (!res.ok) {
        throw new Error('Failed to load audit trail');
      }
      
      const data = await res.json();
      setAuditTrail(data.results || []);
      setAuditPagination({
        total: data.count,
        page: data.page,
        pageSize: data.page_size,
        totalPages: data.total_pages
      });
    } catch (err) {
      setError(err.message);
    }
  };

  const applyAuditFilters = () => {
    setAuditFilters({ ...auditFilters, page: 1 });
    setTimeout(loadAuditTrail, 100);
  };

  const handleAuditPageChange = (newPage) => {
    setAuditFilters({ ...auditFilters, page: newPage });
    setTimeout(loadAuditTrail, 100);
  };

  // API #10: Object history timeline
  const loadObjectHistory = async () => {
    if (!historyModel || !historyObjectId) {
      setError('Please provide both model name and object ID');
      return;
    }
    
    try {
      const res = await fetch(`${API_BASE}/audit/object/${historyModel}/${historyObjectId}/`, {
        headers: authHeaders()
      });
      
      if (!res.ok) {
        throw new Error('Failed to load object history');
      }
      
      const data = await res.json();
      setObjectHistory(data);
      setShowObjectHistory(true);
    } catch (err) {
      setError(err.message);
    }
  };

  // ================= UTILITY FUNCTIONS =================
  
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getStatusBadge = (statusCode) => {
    if (statusCode >= 200 && statusCode < 300) return 'success';
    if (statusCode >= 300 && statusCode < 400) return 'info';
    if (statusCode >= 400 && statusCode < 500) return 'warning';
    return 'danger';
  };

  const getActionBadge = (action) => {
    switch (action) {
      case 'CREATE': return 'success';
      case 'UPDATE': return 'primary';
      case 'DELETE': return 'danger';
      case 'READ': return 'info';
      default: return 'secondary';
    }
  };

  const getResponseTimeBadge = (ms) => {
    if (ms < 100) return 'success';
    if (ms < 250) return 'info';
    if (ms < 500) return 'warning';
    return 'danger';
  };

  // ================= RENDER =================

  if (!hasAccess) {
    return (
      <div className="container mt-4">
        <Alert variant="danger">
          Access Denied: Only Admin and HR can view Activity Logs & Audit Trail
        </Alert>
      </div>
    );
  }

  return (
    <div className="container-fluid mt-4">
      <h3>Activity Logs & Audit Trail</h3>
      
      {error && (
        <Alert variant="danger" onClose={() => setError("")} dismissible>
          {error}
        </Alert>
      )}

      <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k)} className="mb-3">
        
        {/* ========== ACTIVITY LOGS TAB ========== */}
        <Tab eventKey="activity" title="Activity Logs">
          <div className="card mb-3">
            <div className="card-body">
              <h5>Filters</h5>
              <div className="row g-2">
                <div className="col-md-2">
                  <Form.Control
                    size="sm"
                    placeholder="User ID"
                    value={logFilters.user_id}
                    onChange={(e) => setLogFilters({ ...logFilters, user_id: e.target.value })}
                  />
                </div>
                <div className="col-md-2">
                  <Form.Select
                    size="sm"
                    value={logFilters.action}
                    onChange={(e) => setLogFilters({ ...logFilters, action: e.target.value })}
                  >
                    <option value="">All Actions</option>
                    <option value="CREATE">CREATE</option>
                    <option value="READ">READ</option>
                    <option value="UPDATE">UPDATE</option>
                    <option value="DELETE">DELETE</option>
                  </Form.Select>
                </div>
                <div className="col-md-2">
                  <Form.Select
                    size="sm"
                    value={logFilters.method}
                    onChange={(e) => setLogFilters({ ...logFilters, method: e.target.value })}
                  >
                    <option value="">All Methods</option>
                    <option value="GET">GET</option>
                    <option value="POST">POST</option>
                    <option value="PUT">PUT</option>
                    <option value="PATCH">PATCH</option>
                    <option value="DELETE">DELETE</option>
                  </Form.Select>
                </div>
                <div className="col-md-2">
                  <Form.Control
                    size="sm"
                    placeholder="Model Name"
                    value={logFilters.model_name}
                    onChange={(e) => setLogFilters({ ...logFilters, model_name: e.target.value })}
                  />
                </div>
                <div className="col-md-2">
                  <Form.Control
                    size="sm"
                    placeholder="Status Code"
                    value={logFilters.status_code}
                    onChange={(e) => setLogFilters({ ...logFilters, status_code: e.target.value })}
                  />
                </div>
                <div className="col-md-2">
                  <Form.Control
                    size="sm"
                    type="date"
                    value={logFilters.start_date}
                    onChange={(e) => setLogFilters({ ...logFilters, start_date: e.target.value })}
                  />
                </div>
                <div className="col-md-2">
                  <Form.Control
                    size="sm"
                    type="date"
                    value={logFilters.end_date}
                    onChange={(e) => setLogFilters({ ...logFilters, end_date: e.target.value })}
                  />
                </div>
                <div className="col-md-2">
                  <Button size="sm" variant="primary" onClick={applyFilters} className="w-100">
                    Apply
                  </Button>
                </div>
                <div className="col-md-2">
                  <Button size="sm" variant="secondary" onClick={clearFilters} className="w-100">
                    Clear
                  </Button>
                </div>
              </div>
            </div>
          </div>

          <div className="d-flex justify-content-between align-items-center mb-2">
            <small className="text-muted">
              Showing {activityLogs.length} of {logPagination.total} logs
            </small>
            <div className="btn-group btn-group-sm">
              <Button 
                variant="outline-secondary" 
                disabled={logPagination.page <= 1}
                onClick={() => handlePageChange(logPagination.page - 1)}
              >
                Previous
              </Button>
              <Button variant="outline-secondary" disabled>
                Page {logPagination.page} of {logPagination.totalPages}
              </Button>
              <Button 
                variant="outline-secondary"
                disabled={logPagination.page >= logPagination.totalPages}
                onClick={() => handlePageChange(logPagination.page + 1)}
              >
                Next
              </Button>
            </div>
          </div>

          <Table bordered hover size="sm" responsive>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>User</th>
                <th>Action</th>
                <th>Method</th>
                <th>Endpoint</th>
                <th>Status</th>
                <th>Response Time</th>
                <th>Model</th>
                <th>IP</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {activityLogs.length === 0 && (
                <tr>
                  <td colSpan="10" className="text-center">No activity logs found</td>
                </tr>
              )}
              {activityLogs.map((log) => (
                <tr key={log.id}>
                  <td>{formatTimestamp(log.timestamp)}</td>
                  <td>{log.user_name || 'System'}</td>
                  <td>
                    <Badge bg={getActionBadge(log.action)}>{log.action}</Badge>
                  </td>
                  <td><code>{log.method}</code></td>
                  <td><small>{log.endpoint}</small></td>
                  <td>
                    <Badge bg={getStatusBadge(log.status_code)}>{log.status_code}</Badge>
                  </td>
                  <td>
                    <Badge bg={getResponseTimeBadge(log.response_time)}>
                      {log.response_time}ms
                    </Badge>
                  </td>
                  <td>{log.model_name || '-'}</td>
                  <td><small>{log.ip_address}</small></td>
                  <td>
                    <Button size="sm" variant="outline-info" onClick={() => viewLogDetail(log)}>
                      Details
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Tab>

        {/* ========== SEARCH TAB ========== */}
        <Tab eventKey="search" title="Search">
          <div className="card mb-3">
            <div className="card-body">
              <h5>Full-Text Search</h5>
              <div className="row g-2">
                <div className="col-md-10">
                  <Form.Control
                    placeholder="Search logs... (user, endpoint, model, action)"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && performSearch(1)}
                  />
                </div>
                <div className="col-md-2">
                  <Button variant="primary" className="w-100" onClick={() => performSearch(1)}>
                    Search
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {searchResults.length > 0 && (
            <>
              <div className="d-flex justify-content-between align-items-center mb-2">
                <small className="text-muted">
                  Found {searchPagination.total} results
                </small>
                <div className="btn-group btn-group-sm">
                  <Button 
                    variant="outline-secondary" 
                    disabled={searchPagination.page <= 1}
                    onClick={() => performSearch(searchPagination.page - 1)}
                  >
                    Previous
                  </Button>
                  <Button variant="outline-secondary" disabled>
                    Page {searchPagination.page} of {searchPagination.totalPages}
                  </Button>
                  <Button 
                    variant="outline-secondary"
                    disabled={searchPagination.page >= searchPagination.totalPages}
                    onClick={() => performSearch(searchPagination.page + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>

              <Table bordered hover size="sm" responsive>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Endpoint</th>
                    <th>Status</th>
                    <th>Model</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {searchResults.map((log) => (
                    <tr key={log.id}>
                      <td>{formatTimestamp(log.timestamp)}</td>
                      <td>{log.user_name || 'System'}</td>
                      <td>
                        <Badge bg={getActionBadge(log.action)}>{log.action}</Badge>
                      </td>
                      <td><small>{log.endpoint}</small></td>
                      <td>
                        <Badge bg={getStatusBadge(log.status_code)}>{log.status_code}</Badge>
                      </td>
                      <td>{log.model_name || '-'}</td>
                      <td>
                        <Button size="sm" variant="outline-info" onClick={() => viewLogDetail(log)}>
                          Details
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </>
          )}
        </Tab>

        {/* ========== ANALYTICS TAB ========== */}
        <Tab eventKey="analytics" title="Analytics">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5>Usage Statistics</h5>
            <div className="btn-group btn-group-sm">
              <Button 
                variant={statsDays === 7 ? 'primary' : 'outline-primary'}
                onClick={() => changeStatsPeriod(7)}
              >
                Last 7 Days
              </Button>
              <Button 
                variant={statsDays === 14 ? 'primary' : 'outline-primary'}
                onClick={() => changeStatsPeriod(14)}
              >
                Last 14 Days
              </Button>
              <Button 
                variant={statsDays === 30 ? 'primary' : 'outline-primary'}
                onClick={() => changeStatsPeriod(30)}
              >
                Last 30 Days
              </Button>
            </div>
          </div>

          {stats && (
            <>
              <div className="row mb-4">
                <div className="col-md-3">
                  <div className="card text-center">
                    <div className="card-body">
                      <h2 className="text-primary">{stats.total_logs}</h2>
                      <p className="text-muted mb-0">Total Logs</p>
                    </div>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="card text-center">
                    <div className="card-body">
                      <h2 className="text-success">{stats.total_users}</h2>
                      <p className="text-muted mb-0">Active Users</p>
                    </div>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="card text-center">
                    <div className="card-body">
                      <h2 className="text-info">{stats.average_response_time?.toFixed(2)}ms</h2>
                      <p className="text-muted mb-0">Avg Response Time</p>
                    </div>
                  </div>
                </div>
                <div className="col-md-3">
                  <div className="card text-center">
                    <div className="card-body">
                      <h2 className="text-danger">{stats.recent_errors?.length || 0}</h2>
                      <p className="text-muted mb-0">Recent Errors</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="row mb-4">
                <div className="col-md-6">
                  <div className="card">
                    <div className="card-header">
                      <strong>Actions Breakdown</strong>
                    </div>
                    <div className="card-body">
                      {Object.entries(stats.actions_breakdown || {}).map(([action, count]) => (
                        <div key={action} className="mb-2">
                          <div className="d-flex justify-content-between mb-1">
                            <span><Badge bg={getActionBadge(action)}>{action}</Badge></span>
                            <span>{count}</span>
                          </div>
                          <ProgressBar 
                            now={(count / stats.total_logs) * 100} 
                            variant={getActionBadge(action)}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="col-md-6">
                  <div className="card">
                    <div className="card-header">
                      <strong>Status Codes Breakdown</strong>
                    </div>
                    <div className="card-body">
                      {Object.entries(stats.status_codes_breakdown || {}).map(([code, count]) => (
                        <div key={code} className="mb-2">
                          <div className="d-flex justify-content-between mb-1">
                            <span><Badge bg={getStatusBadge(parseInt(code))}>{code}</Badge></span>
                            <span>{count}</span>
                          </div>
                          <ProgressBar 
                            now={(count / stats.total_logs) * 100}
                            variant={getStatusBadge(parseInt(code))}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {stats.recent_errors && stats.recent_errors.length > 0 && (
                <div className="card">
                  <div className="card-header">
                    <strong>Recent Errors</strong>
                  </div>
                  <div className="card-body">
                    <Table bordered size="sm">
                      <thead>
                        <tr>
                          <th>Timestamp</th>
                          <th>User</th>
                          <th>Endpoint</th>
                          <th>Status</th>
                          <th>Error</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stats.recent_errors.map((error, idx) => (
                          <tr key={idx}>
                            <td>{formatTimestamp(error.timestamp)}</td>
                            <td>{error.user_name || 'Unknown'}</td>
                            <td><small>{error.endpoint}</small></td>
                            <td>
                              <Badge bg="danger">{error.status_code}</Badge>
                            </td>
                            <td><small>{error.error_message || 'N/A'}</small></td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </div>
                </div>
              )}
            </>
          )}
        </Tab>

        {/* ========== AUDIT TRAIL TAB ========== */}
        <Tab eventKey="audit" title="Audit Trail">
          <div className="card mb-3">
            <div className="card-body">
              <h5>Filters</h5>
              <div className="row g-2">
                <div className="col-md-3">
                  <Form.Control
                    size="sm"
                    placeholder="Model Name"
                    value={auditFilters.model_name}
                    onChange={(e) => setAuditFilters({ ...auditFilters, model_name: e.target.value })}
                  />
                </div>
                <div className="col-md-3">
                  <Form.Select
                    size="sm"
                    value={auditFilters.action}
                    onChange={(e) => setAuditFilters({ ...auditFilters, action: e.target.value })}
                  >
                    <option value="">All Actions</option>
                    <option value="CREATE">CREATE</option>
                    <option value="UPDATE">UPDATE</option>
                    <option value="DELETE">DELETE</option>
                  </Form.Select>
                </div>
                <div className="col-md-2">
                  <Button size="sm" variant="primary" onClick={applyAuditFilters} className="w-100">
                    Apply
                  </Button>
                </div>
              </div>

              <hr />

              <h5>Object History Lookup</h5>
              <div className="row g-2">
                <div className="col-md-3">
                  <Form.Control
                    size="sm"
                    placeholder="Model Name (e.g., Employee)"
                    value={historyModel}
                    onChange={(e) => setHistoryModel(e.target.value)}
                  />
                </div>
                <div className="col-md-3">
                  <Form.Control
                    size="sm"
                    placeholder="Object ID"
                    value={historyObjectId}
                    onChange={(e) => setHistoryObjectId(e.target.value)}
                  />
                </div>
                <div className="col-md-2">
                  <Button size="sm" variant="info" onClick={loadObjectHistory} className="w-100">
                    View History
                  </Button>
                </div>
              </div>
            </div>
          </div>

          <div className="d-flex justify-content-between align-items-center mb-2">
            <small className="text-muted">
              Showing {auditTrail.length} of {auditPagination.total} audit records
            </small>
            <div className="btn-group btn-group-sm">
              <Button 
                variant="outline-secondary" 
                disabled={auditPagination.page <= 1}
                onClick={() => handleAuditPageChange(auditPagination.page - 1)}
              >
                Previous
              </Button>
              <Button variant="outline-secondary" disabled>
                Page {auditPagination.page} of {auditPagination.totalPages}
              </Button>
              <Button 
                variant="outline-secondary"
                disabled={auditPagination.page >= auditPagination.totalPages}
                onClick={() => handleAuditPageChange(auditPagination.page + 1)}
              >
                Next
              </Button>
            </div>
          </div>

          <Table bordered hover size="sm" responsive>
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>User</th>
                <th>Action</th>
                <th>Model</th>
                <th>Object ID</th>
                <th>Changes</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {auditTrail.length === 0 && (
                <tr>
                  <td colSpan="7" className="text-center">No audit records found</td>
                </tr>
              )}
              {auditTrail.map((audit) => (
                <tr key={audit.id}>
                  <td>{formatTimestamp(audit.timestamp)}</td>
                  <td>{audit.user_name || 'System'}</td>
                  <td>
                    <Badge bg={getActionBadge(audit.action)}>{audit.action}</Badge>
                  </td>
                  <td>{audit.model_name}</td>
                  <td>{audit.object_id}</td>
                  <td>
                    {audit.changes ? (
                      <small>{Object.keys(JSON.parse(audit.changes)).join(', ')}</small>
                    ) : '-'}
                  </td>
                  <td>
                    <Button size="sm" variant="outline-info" onClick={() => viewLogDetail(audit)}>
                      Details
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Tab>
      </Tabs>

      {/* ========== LOG DETAIL MODAL ========== */}
      <Modal show={showLogDetail} onHide={() => setShowLogDetail(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Log Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedLog && (
            <div>
              <p><strong>Timestamp:</strong> {formatTimestamp(selectedLog.timestamp)}</p>
              <p><strong>User:</strong> {selectedLog.user_name || 'System'}</p>
              <p><strong>Action:</strong> <Badge bg={getActionBadge(selectedLog.action)}>{selectedLog.action}</Badge></p>
              <p><strong>Method:</strong> <code>{selectedLog.method}</code></p>
              <p><strong>Endpoint:</strong> <code>{selectedLog.endpoint}</code></p>
              <p><strong>Status Code:</strong> <Badge bg={getStatusBadge(selectedLog.status_code)}>{selectedLog.status_code}</Badge></p>
              <p><strong>Response Time:</strong> {selectedLog.response_time}ms</p>
              <p><strong>Model:</strong> {selectedLog.model_name || 'N/A'}</p>
              <p><strong>Object ID:</strong> {selectedLog.object_id || 'N/A'}</p>
              <p><strong>IP Address:</strong> {selectedLog.ip_address}</p>
              
              {selectedLog.request_data && (
                <>
                  <hr />
                  <h6>Request Data:</h6>
                  <pre style={{maxHeight: '200px', overflow: 'auto', backgroundColor: '#f5f5f5', padding: '10px'}}>
                    {JSON.stringify(JSON.parse(selectedLog.request_data), null, 2)}
                  </pre>
                </>
              )}
              
              {selectedLog.response_data && (
                <>
                  <hr />
                  <h6>Response Data:</h6>
                  <pre style={{maxHeight: '200px', overflow: 'auto', backgroundColor: '#f5f5f5', padding: '10px'}}>
                    {JSON.stringify(JSON.parse(selectedLog.response_data), null, 2)}
                  </pre>
                </>
              )}
              
              {selectedLog.error_message && (
                <>
                  <hr />
                  <h6 className="text-danger">Error Message:</h6>
                  <Alert variant="danger">{selectedLog.error_message}</Alert>
                </>
              )}
              
              {selectedLog.changes && (
                <>
                  <hr />
                  <h6>Changes:</h6>
                  <pre style={{maxHeight: '200px', overflow: 'auto', backgroundColor: '#f5f5f5', padding: '10px'}}>
                    {JSON.stringify(JSON.parse(selectedLog.changes), null, 2)}
                  </pre>
                </>
              )}
            </div>
          )}
        </Modal.Body>
      </Modal>

      {/* ========== OBJECT HISTORY MODAL ========== */}
      <Modal show={showObjectHistory} onHide={() => setShowObjectHistory(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Object History Timeline</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {objectHistory && (
            <>
              <p><strong>Model:</strong> {objectHistory.model_name}</p>
              <p><strong>Object ID:</strong> {objectHistory.object_id}</p>
              <p><strong>Total Changes:</strong> {objectHistory.count}</p>
              <hr />
              
              {objectHistory.results && objectHistory.results.length > 0 ? (
                <div style={{maxHeight: '400px', overflow: 'auto'}}>
                  {objectHistory.results.map((record, idx) => (
                    <div key={idx} className="mb-3 p-3 border rounded">
                      <div className="d-flex justify-content-between align-items-center mb-2">
                        <Badge bg={getActionBadge(record.action)}>{record.action}</Badge>
                        <small className="text-muted">{formatTimestamp(record.timestamp)}</small>
                      </div>
                      <p className="mb-1"><strong>User:</strong> {record.user_name || 'System'}</p>
                      {record.changes && (
                        <>
                          <p className="mb-1"><strong>Fields Changed:</strong></p>
                          <pre style={{fontSize: '0.85rem', backgroundColor: '#f5f5f5', padding: '8px'}}>
                            {JSON.stringify(JSON.parse(record.changes), null, 2)}
                          </pre>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted">No history records found</p>
              )}
            </>
          )}
        </Modal.Body>
      </Modal>
    </div>
  );
}

export default LogsPanel;
