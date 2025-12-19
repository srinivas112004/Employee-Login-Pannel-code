import React, { useState, useEffect } from "react";
import { Table, Button, Badge, Modal, Form, Alert, Tabs, Tab, ProgressBar } from "react-bootstrap";
import { useAuth } from "../context/AuthContext";

const API_BASE = "http://localhost:8000/api/documents";

/* ================= AUTH HEADERS ================= */
const authHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem("access_token")}`,
});

const authHeadersJSON = () => ({
  Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  "Content-Type": "application/json",
});

export default function DocumentsPanel() {
  /* ================= AUTH & ROLE ================= */
  const { user } = useAuth();
  const role = (user?.role || "").toLowerCase();
  const isAdminOrHR = role === "admin" || role === "hr";

  // State for Categories
  const [categories, setCategories] = useState([]);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [categoryForm, setCategoryForm] = useState({ id: null, name: "", description: "", icon: "" });
  
  // State for Documents
  const [documents, setDocuments] = useState([]);
  const [myDocuments, setMyDocuments] = useState([]);
  const [sharedWithMe, setSharedWithMe] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showDocumentModal, setShowDocumentModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [showVersionsModal, setShowVersionsModal] = useState(false);
  const [showAccessLogsModal, setShowAccessLogsModal] = useState(false);
  
  // Document form
  const [documentForm, setDocumentForm] = useState({
    id: null,
    title: "",
    description: "",
    category: "",
    tags: "",
    access_level: "private",
    file: null
  });

  // Share form
  const [shareForm, setShareForm] = useState({
    shared_with: "",
    can_edit: false,
    can_download: true,
    expires_at: ""
  });

  // Versions and logs
  const [versions, setVersions] = useState([]);
  const [accessLogs, setAccessLogs] = useState([]);
  const [shares, setShares] = useState([]);
  
  // UI State
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [activeTab, setActiveTab] = useState("all");
  const [filterCategory, setFilterCategory] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    loadCategories();
    loadDocuments();
    loadMyDocuments();
    loadSharedWithMe();
    loadShares();
  }, []);

  // ================= DOCUMENT CATEGORIES (APIs 1-5) =================
  
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
        headers: authHeadersJSON(),
        body: JSON.stringify({
          name: categoryForm.name,
          description: categoryForm.description,
          icon: categoryForm.icon
        })
      });
      
      if (!res.ok) throw new Error('Failed to save category');
      
      setSuccess(categoryForm.id ? 'Category updated' : 'Category created');
      setShowCategoryModal(false);
      setCategoryForm({ id: null, name: "", description: "", icon: "" });
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

  // ================= DOCUMENT MANAGEMENT (APIs 6-10) =================
  
  // API #6: List documents
  const loadDocuments = async () => {
    try {
      const params = new URLSearchParams();
      if (filterCategory) params.append('category', filterCategory);
      if (searchQuery) params.append('search', searchQuery);
      
      const res = await fetch(`${API_BASE}/documents/?${params}`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load documents');
      const data = await res.json();
      setDocuments(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError(err.message);
    }
  };

  // API #7: Upload document
  const uploadDocument = async () => {
    try {
      const formData = new FormData();
      formData.append('title', documentForm.title);
      formData.append('description', documentForm.description);
      formData.append('category', documentForm.category);
      formData.append('tags', documentForm.tags);
      formData.append('access_level', documentForm.access_level);
      if (documentForm.file) {
        formData.append('file', documentForm.file);
      }
      
      const res = await fetch(`${API_BASE}/documents/`, {
        method: 'POST',
        headers: authHeaders(),
        body: formData
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to upload document');
      }
      
      setSuccess('Document uploaded successfully');
      setShowUploadModal(false);
      resetDocumentForm();
      loadDocuments();
      loadMyDocuments();
    } catch (err) {
      setError(err.message);
    }
  };

  // API #8: Get document details
  const viewDocumentDetails = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/documents/${id}/`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load document details');
      const data = await res.json();
      setSelectedDocument(data);
      setShowDocumentModal(true);
    } catch (err) {
      setError(err.message);
    }
  };

  // API #9: Update document
  const updateDocument = async () => {
    try {
      const formData = new FormData();
      formData.append('title', documentForm.title);
      formData.append('description', documentForm.description);
      formData.append('category', documentForm.category);
      formData.append('tags', documentForm.tags);
      formData.append('access_level', documentForm.access_level);
      if (documentForm.file) {
        formData.append('file', documentForm.file);
      }
      
      const res = await fetch(`${API_BASE}/documents/${documentForm.id}/`, {
        method: 'PUT',
        headers: authHeaders(),
        body: formData
      });
      
      if (!res.ok) throw new Error('Failed to update document');
      
      setSuccess('Document updated successfully');
      setShowUploadModal(false);
      resetDocumentForm();
      loadDocuments();
      loadMyDocuments();
    } catch (err) {
      setError(err.message);
    }
  };

  // API #10: Delete document
  const deleteDocument = async (id) => {
    if (!window.confirm('Delete this document?')) return;
    try {
      const res = await fetch(`${API_BASE}/documents/${id}/`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to delete document');
      setSuccess('Document deleted');
      loadDocuments();
      loadMyDocuments();
    } catch (err) {
      setError(err.message);
    }
  };

  // ================= DOCUMENT ACTIONS (APIs 11-17) =================
  
  // API #11: Download document
  const downloadDocument = async (id, title) => {
    try {
      const res = await fetch(`${API_BASE}/documents/${id}/download/`, {
        headers: authHeaders()
      });
      
      const blob = await res.blob();
      
      // If we got a blob with content, proceed with download regardless of status
      if (blob.size > 0) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = title || 'document';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        setSuccess('Document downloaded');
      } else {
        throw new Error('Downloaded file is empty');
      }
    } catch (err) {
      // Only show error if it's not a network error and blob wasn't created
      if (!err.message.includes('Failed to fetch')) {
        setError(err.message || 'Failed to download document');
      }
    }
  };

  // API #12: List versions
  const loadVersions = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/documents/${id}/versions/`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load versions');
      const data = await res.json();
      setVersions(Array.isArray(data) ? data : data.results || []);
      setShowVersionsModal(true);
    } catch (err) {
      setError(err.message);
    }
  };

  // API #13: Download specific version
  const downloadVersion = async (docId, version, title) => {
    try {
      const res = await fetch(`${API_BASE}/documents/${docId}/versions/${version}/download/`, {
        headers: authHeaders()
      });
      
      const blob = await res.blob();
      
      // If we got a blob with content, proceed with download regardless of status
      if (blob.size > 0) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title}_v${version}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        setSuccess(`Version ${version} downloaded`);
      } else {
        throw new Error('Downloaded file is empty');
      }
    } catch (err) {
      // Only show error if it's not a network error and blob wasn't created
      if (!err.message.includes('Failed to fetch')) {
        setError(err.message || 'Failed to download version');
      }
    }
  };

  // API #14: Share document
  const shareDocument = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents/${selectedDocument.id}/share/`, {
        method: 'POST',
        headers: authHeadersJSON(),
        body: JSON.stringify(shareForm)
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to share document');
      }
      
      setSuccess('Document shared successfully');
      setShowShareModal(false);
      setShareForm({ shared_with: "", can_edit: false, can_download: true, expires_at: "" });
      loadShares();
    } catch (err) {
      setError(err.message);
    }
  };

  // API #15: Archive document
  const archiveDocument = async (id) => {
    if (!window.confirm('Archive this document?')) return;
    try {
      const res = await fetch(`${API_BASE}/documents/${id}/archive/`, {
        method: 'POST',
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to archive document');
      setSuccess('Document archived');
      loadDocuments();
      loadMyDocuments();
    } catch (err) {
      setError(err.message);
    }
  };

  // API #16: Restore document
  const restoreDocument = async (id) => {
    if (!window.confirm('Restore this document?')) return;
    try {
      const res = await fetch(`${API_BASE}/documents/${id}/restore/`, {
        method: 'POST',
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to restore document');
      setSuccess('Document restored');
      loadDocuments();
      loadMyDocuments();
    } catch (err) {
      setError(err.message);
    }
  };

  // API #17: View access logs
  const loadAccessLogs = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/documents/${id}/access_logs/`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load access logs');
      const data = await res.json();
      setAccessLogs(Array.isArray(data) ? data : data.results || []);
      setShowAccessLogsModal(true);
    } catch (err) {
      setError(err.message);
    }
  };

  // ================= DOCUMENT VIEWS (APIs 18-19) =================
  
  // API #18: My documents
  const loadMyDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents/my_documents/`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load my documents');
      const data = await res.json();
      setMyDocuments(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError(err.message);
    }
  };

  // API #19: Shared with me
  const loadSharedWithMe = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents/shared_with_me/`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load shared documents');
      const data = await res.json();
      setSharedWithMe(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError(err.message);
    }
  };

  // ================= DOCUMENT SHARES (APIs 20-21) =================
  
  // API #20: List shares
  const loadShares = async () => {
    try {
      const res = await fetch(`${API_BASE}/shares/`, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to load shares');
      const data = await res.json();
      setShares(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError(err.message);
    }
  };

  // ================= UTILITY FUNCTIONS =================
  
  const resetDocumentForm = () => {
    setDocumentForm({
      id: null,
      title: "",
      description: "",
      category: "",
      tags: "",
      access_level: "private",
      file: null
    });
  };

  const openEditDocument = (doc) => {
    setDocumentForm({
      id: doc.id,
      title: doc.title,
      description: doc.description,
      category: doc.category,
      tags: doc.tags?.join(', ') || "",
      access_level: doc.access_level,
      file: null
    });
    setShowUploadModal(true);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'archived': return 'warning';
      default: return 'secondary';
    }
  };

  const getAccessLevelBadge = (access_level) => {
    switch (access_level) {
      case 'company': return 'info';
      case 'department': return 'primary';
      case 'team': return 'warning';
      case 'private': return 'secondary';
      default: return 'secondary';
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  // ================= RENDER =================

  const renderDocumentTable = (docs) => (
    <Table bordered hover size="sm" responsive>
      <thead>
        <tr>
          <th>Title</th>
          <th>Category</th>
          <th>Owner</th>
          <th>Size</th>
          <th>Version</th>
          <th>Status</th>
          <th>Access Level</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {docs.length === 0 && (
          <tr>
            <td colSpan="8" className="text-center">No documents found</td>
          </tr>
        )}
        {docs.map((doc) => (
          <tr key={doc.id}>
            <td>
              <div>
                <strong>{doc.title}</strong>
                {doc.tags && doc.tags.length > 0 && (
                  <div className="mt-1">
                    {doc.tags.map((tag, idx) => (
                      <Badge key={idx} bg="light" text="dark" className="me-1" style={{fontSize: '10px'}}>
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </td>
            <td>{doc.category_name || doc.category}</td>
            <td>{doc.uploaded_by_name || doc.uploaded_by}</td>
            <td>{formatFileSize(doc.file_size)}</td>
            <td>{doc.current_version}</td>
            <td>
              <Badge bg={getStatusBadge(doc.status)}>{doc.status}</Badge>
            </td>
            <td>
              <Badge bg={getAccessLevelBadge(doc.access_level)}>{doc.access_level}</Badge>
            </td>
            <td>
              <div className="btn-group-vertical btn-group-sm" role="group">
                <Button size="sm" variant="outline-info" onClick={() => viewDocumentDetails(doc.id)}>
                  View
                </Button>
                <Button size="sm" variant="outline-success" onClick={() => downloadDocument(doc.id, doc.title)}>
                  Download
                </Button>
                <Button size="sm" variant="outline-secondary" onClick={() => loadVersions(doc.id)}>
                  Versions
                </Button>
                {(doc.can_edit || isAdminOrHR) && (
                  <>
                    <Button size="sm" variant="outline-primary" onClick={() => openEditDocument(doc)}>
                      Edit
                    </Button>
                    <Button size="sm" variant="outline-warning" onClick={() => {
                      setSelectedDocument(doc);
                      setShowShareModal(true);
                    }}>
                      Share
                    </Button>
                    {doc.status === 'active' && (
                      <Button size="sm" variant="outline-dark" onClick={() => archiveDocument(doc.id)}>
                        Archive
                      </Button>
                    )}
                    {doc.status === 'archived' && (
                      <Button size="sm" variant="outline-success" onClick={() => restoreDocument(doc.id)}>
                        Restore
                      </Button>
                    )}
                    <Button size="sm" variant="outline-info" onClick={() => loadAccessLogs(doc.id)}>
                      Logs
                    </Button>
                    <Button size="sm" variant="outline-danger" onClick={() => deleteDocument(doc.id)}>
                      Delete
                    </Button>
                  </>
                )}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );

  return (
    <div className="container-fluid mt-4">
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
        
        {/* ========== ALL DOCUMENTS TAB ========== */}
        <Tab eventKey="all" title="All Documents">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <div className="d-flex gap-2 align-items-center">
              <h5 className="mb-0">All Documents</h5>
              <Form.Select 
                size="sm" 
                style={{width: '200px'}}
                value={filterCategory}
                onChange={(e) => {
                  setFilterCategory(e.target.value);
                  setTimeout(() => loadDocuments(), 100);
                }}
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
              </Form.Select>
              <Form.Control
                size="sm"
                type="text"
                placeholder="Search documents..."
                style={{width: '250px'}}
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setTimeout(() => loadDocuments(), 300);
                }}
              />
            </div>
            <Button variant="primary" onClick={() => {
              resetDocumentForm();
              setShowUploadModal(true);
            }}>
              + Upload Document
            </Button>
          </div>

          {renderDocumentTable(documents)}
        </Tab>

        {/* ========== MY DOCUMENTS TAB ========== */}
        <Tab eventKey="my-docs" title={`My Documents (${myDocuments.length})`}>
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5>My Uploaded Documents</h5>
            <Button variant="primary" onClick={() => {
              resetDocumentForm();
              setShowUploadModal(true);
            }}>
              + Upload Document
            </Button>
          </div>

          {renderDocumentTable(myDocuments)}
        </Tab>

        {/* ========== SHARED WITH ME TAB ========== */}
        <Tab eventKey="shared" title={`Shared With Me (${sharedWithMe.length})`}>
          <h5>Documents Shared With Me</h5>

          {renderDocumentTable(sharedWithMe)}
        </Tab>

        {/* ========== CATEGORIES TAB (Admin/HR) ========== */}
        {isAdminOrHR && (
          <Tab eventKey="categories" title="Categories">
            <div className="d-flex justify-content-between align-items-center mb-3">
              <h5>Document Categories</h5>
              <Button variant="primary" onClick={() => {
                setCategoryForm({ id: null, name: "", description: "", icon: "" });
                setShowCategoryModal(true);
              }}>
                + Add Category
              </Button>
            </div>

            <Table bordered hover size="sm">
              <thead>
                <tr>
                  <th>Icon</th>
                  <th>Name</th>
                  <th>Description</th>
                  <th>Documents</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {categories.length === 0 && (
                  <tr>
                    <td colSpan="5" className="text-center">No categories</td>
                  </tr>
                )}
                {categories.map((cat) => (
                  <tr key={cat.id}>
                    <td className="text-center">
                      <i className={`bi bi-${cat.icon || 'folder'}`} style={{fontSize: '20px'}}></i>
                    </td>
                    <td>{cat.name}</td>
                    <td>{cat.description}</td>
                    <td>
                      <Badge bg="info">{cat.document_count || 0}</Badge>
                    </td>
                    <td>
                      <Button 
                        size="sm" 
                        variant="outline-primary" 
                        onClick={() => {
                          setCategoryForm({ 
                            id: cat.id, 
                            name: cat.name, 
                            description: cat.description,
                            icon: cat.icon 
                          });
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

        {/* ========== SHARES TAB ========== */}
        <Tab eventKey="shares" title={`Shares (${shares.length})`}>
          <h5>Document Sharing Activity</h5>

          <Table bordered hover size="sm" responsive>
            <thead>
              <tr>
                <th>Document</th>
                <th>Shared With</th>
                <th>Shared By</th>
                <th>Permissions</th>
                <th>Expires</th>
                <th>Accessed</th>
              </tr>
            </thead>
            <tbody>
              {shares.length === 0 && (
                <tr>
                  <td colSpan="6" className="text-center">No shares</td>
                </tr>
              )}
              {shares.map((share) => (
                <tr key={share.id}>
                  <td>{share.document_title || share.document}</td>
                  <td>{share.shared_with_name || share.shared_with}</td>
                  <td>{share.shared_by_name || share.shared_by}</td>
                  <td>
                    {share.can_edit && <Badge bg="primary" className="me-1">Edit</Badge>}
                    {share.can_download && <Badge bg="success" className="me-1">Download</Badge>}
                    {!share.can_edit && !share.can_download && <Badge bg="secondary">View Only</Badge>}
                  </td>
                  <td>
                    {share.expires_at ? new Date(share.expires_at).toLocaleDateString() : 'Never'}
                  </td>
                  <td>
                    {share.access_count || 0} times
                    {share.last_accessed_at && (
                      <div className="small text-muted">
                        Last: {new Date(share.last_accessed_at).toLocaleString()}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Tab>
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
          <Form.Group className="mb-3">
            <Form.Label>Icon (Bootstrap Icon name)</Form.Label>
            <Form.Control
              value={categoryForm.icon}
              onChange={(e) => setCategoryForm({ ...categoryForm, icon: e.target.value })}
              placeholder="e.g., folder, briefcase, file-text"
            />
            <Form.Text className="text-muted">
              Use Bootstrap Icons: folder, briefcase, file-text, shield, etc.
            </Form.Text>
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

      {/* ========== UPLOAD/EDIT DOCUMENT MODAL ========== */}
      <Modal show={showUploadModal} onHide={() => setShowUploadModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>{documentForm.id ? 'Edit' : 'Upload'} Document</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Title *</Form.Label>
            <Form.Control
              value={documentForm.title}
              onChange={(e) => setDocumentForm({ ...documentForm, title: e.target.value })}
              placeholder="Document title"
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={documentForm.description}
              onChange={(e) => setDocumentForm({ ...documentForm, description: e.target.value })}
              placeholder="Document description"
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Category *</Form.Label>
            <Form.Select
              value={documentForm.category}
              onChange={(e) => setDocumentForm({ ...documentForm, category: e.target.value })}
            >
              <option value="">Select category</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Tags (comma-separated)</Form.Label>
            <Form.Control
              value={documentForm.tags}
              onChange={(e) => setDocumentForm({ ...documentForm, tags: e.target.value })}
              placeholder="e.g., policy, 2025, important"
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Access Level *</Form.Label>
            <Form.Select
              value={documentForm.access_level}
              onChange={(e) => setDocumentForm({ ...documentForm, access_level: e.target.value })}
            >
              <option value="private">Private (Only me)</option>
              <option value="team">Team (Selected users/roles)</option>
              <option value="department">Department (Same department)</option>
              <option value="company">Company-wide (All employees)</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>
              File * {documentForm.id && <small className="text-muted">(Leave empty to keep current file)</small>}
            </Form.Label>
            <Form.Control
              type="file"
              onChange={(e) => setDocumentForm({ ...documentForm, file: e.target.files[0] })}
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowUploadModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={documentForm.id ? updateDocument : uploadDocument}>
            {documentForm.id ? 'Update' : 'Upload'}
          </Button>
        </Modal.Footer>
      </Modal>

      {/* ========== DOCUMENT DETAIL MODAL ========== */}
      <Modal show={showDocumentModal} onHide={() => setShowDocumentModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Document Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedDocument && (
            <>
              <h4>{selectedDocument.title}</h4>
              <p>
                <Badge bg={getStatusBadge(selectedDocument.status)}>{selectedDocument.status}</Badge>
                {' '}
                <Badge bg={getAccessLevelBadge(selectedDocument.access_level)}>{selectedDocument.access_level}</Badge>
              </p>
              <p><strong>Category:</strong> {selectedDocument.category_name || selectedDocument.category}</p>
              <p><strong>Description:</strong> {selectedDocument.description}</p>
              <p><strong>Uploaded by:</strong> {selectedDocument.uploaded_by_name}</p>
              <p><strong>Size:</strong> {formatFileSize(selectedDocument.file_size)}</p>
              <p><strong>Version:</strong> {selectedDocument.current_version}</p>
              <p><strong>Downloads:</strong> {selectedDocument.download_count || 0}</p>
              <p><strong>Created:</strong> {new Date(selectedDocument.created_at).toLocaleString()}</p>
              {selectedDocument.tags && selectedDocument.tags.length > 0 && (
                <p>
                  <strong>Tags:</strong>{' '}
                  {selectedDocument.tags.map((tag, idx) => (
                    <Badge key={idx} bg="light" text="dark" className="me-1">
                      {tag}
                    </Badge>
                  ))}
                </p>
              )}
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowDocumentModal(false)}>
            Close
          </Button>
          {selectedDocument && (
            <Button 
              variant="success" 
              onClick={() => downloadDocument(selectedDocument.id, selectedDocument.title)}
            >
              Download
            </Button>
          )}
        </Modal.Footer>
      </Modal>

      {/* ========== SHARE MODAL ========== */}
      <Modal show={showShareModal} onHide={() => setShowShareModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Share Document</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedDocument && (
            <>
              <Alert variant="info">
                Sharing: <strong>{selectedDocument.title}</strong>
              </Alert>
              <Form.Group className="mb-3">
                <Form.Label>Share with (User ID) *</Form.Label>
                <Form.Control
                  type="number"
                  value={shareForm.shared_with}
                  onChange={(e) => setShareForm({ ...shareForm, shared_with: e.target.value })}
                  placeholder="Enter user ID"
                />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Check
                  type="checkbox"
                  label="Allow editing"
                  checked={shareForm.can_edit}
                  onChange={(e) => setShareForm({ ...shareForm, can_edit: e.target.checked })}
                />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Check
                  type="checkbox"
                  label="Allow downloading"
                  checked={shareForm.can_download}
                  onChange={(e) => setShareForm({ ...shareForm, can_download: e.target.checked })}
                />
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Expires at (optional)</Form.Label>
                <Form.Control
                  type="datetime-local"
                  value={shareForm.expires_at}
                  onChange={(e) => setShareForm({ ...shareForm, expires_at: e.target.value })}
                />
              </Form.Group>
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowShareModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={shareDocument}>
            Share
          </Button>
        </Modal.Footer>
      </Modal>

      {/* ========== VERSIONS MODAL ========== */}
      <Modal show={showVersionsModal} onHide={() => setShowVersionsModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Document Versions</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Table bordered size="sm">
            <thead>
              <tr>
                <th>Version</th>
                <th>Uploaded</th>
                <th>Size</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {versions.length === 0 && (
                <tr>
                  <td colSpan="4" className="text-center">No versions</td>
                </tr>
              )}
              {versions.map((ver) => (
                <tr key={ver.version_number}>
                  <td>
                    <strong>v{ver.version_number}</strong>
                    {ver.is_current && <Badge bg="success" className="ms-2">Current</Badge>}
                  </td>
                  <td>{new Date(ver.uploaded_at).toLocaleString()}</td>
                  <td>{formatFileSize(ver.file_size)}</td>
                  <td>
                    <Button 
                      size="sm" 
                      variant="outline-success"
                      onClick={() => downloadVersion(ver.document, ver.version_number, 'document')}
                    >
                      Download
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowVersionsModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>

      {/* ========== ACCESS LOGS MODAL ========== */}
      <Modal show={showAccessLogsModal} onHide={() => setShowAccessLogsModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Access Logs</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Table bordered size="sm">
            <thead>
              <tr>
                <th>User</th>
                <th>Action</th>
                <th>Timestamp</th>
                <th>IP Address</th>
              </tr>
            </thead>
            <tbody>
              {accessLogs.length === 0 && (
                <tr>
                  <td colSpan="4" className="text-center">No access logs</td>
                </tr>
              )}
              {accessLogs.map((log, idx) => (
                <tr key={idx}>
                  <td>{log.user_name || log.user}</td>
                  <td>
                    <Badge bg={log.action === 'download' ? 'success' : 'info'}>
                      {log.action}
                    </Badge>
                  </td>
                  <td>{new Date(log.accessed_at).toLocaleString()}</td>
                  <td>{log.ip_address || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAccessLogsModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}
