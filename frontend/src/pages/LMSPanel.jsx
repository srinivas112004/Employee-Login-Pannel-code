// src/pages/LMSPanel.jsx
// Day 20 – Learning Management System (LMS)
// FULLY ROLE-BASED + AUTHENTICATION SAFE

import React, { useEffect, useState } from "react";
import { Table, Button, Modal, ProgressBar, Badge, Alert, Form } from "react-bootstrap";
import { useAuth } from "../context/AuthContext";

const API_BASE = "http://localhost:8000/api/lms";

/* ================= AUTH HEADERS ================= */
const authHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  "Content-Type": "application/json",
});

export default function LMSPanel() {
  /* ================= AUTH & ROLE ================= */
  const { user } = useAuth();
  const role = (user?.role || "").toLowerCase();
  // employee | manager | hr | admin
  console.log("LMSPanel - User:", user, "Role:", role);

  /* ================= STATE ================= */
  const [courses, setCourses] = useState([]);
  const [myCourses, setMyCourses] = useState([]);
  const [pending, setPending] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [modules, setModules] = useState([]);
  const [courseStats, setCourseStats] = useState(null);
  const [myProgress, setMyProgress] = useState([]);
  
  // Day 21 - Quizzes
  const [quizzes, setQuizzes] = useState([]);
  const [selectedQuiz, setSelectedQuiz] = useState(null);
  const [quizAttempts, setQuizAttempts] = useState([]);
  const [currentAttempt, setCurrentAttempt] = useState(null);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [leaderboard, setLeaderboard] = useState([]);
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [selectedQuizForQuestions, setSelectedQuizForQuestions] = useState(null);
  
  // Day 21 - Certificates
  const [certificates, setCertificates] = useState([]);
  const [myCertificates, setMyCertificates] = useState([]);
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  
  // Day 21 - Skills
  const [skills, setSkills] = useState([]);
  const [mySkills, setMySkills] = useState([]);
  const [skillGapAnalysis, setSkillGapAnalysis] = useState(null);
  
  const [activeTab, setActiveTab] = useState('courses'); // courses, quizzes, certificates, skills
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [showCreate, setShowCreate] = useState(false);
  const [showCourseDetail, setShowCourseDetail] = useState(false);
  const [showCourseEdit, setShowCourseEdit] = useState(false);
  const [showModuleCreate, setShowModuleCreate] = useState(false);
  const [showModuleEdit, setShowModuleEdit] = useState(false);
  const [showModuleDetail, setShowModuleDetail] = useState(false);
  const [showAllModules, setShowAllModules] = useState(false);
  const [showAllEnrollments, setShowAllEnrollments] = useState(false);
  const [showEnrollmentCreate, setShowEnrollmentCreate] = useState(false);
  const [showEnrollmentDetail, setShowEnrollmentDetail] = useState(false);
  const [showEnrollmentEdit, setShowEnrollmentEdit] = useState(false);
  const [showAllProgress, setShowAllProgress] = useState(false);
  const [showStats, setShowStats] = useState(false);
  const [showProgress, setShowProgress] = useState(false);
  const [showQuizCreate, setShowQuizCreate] = useState(false);
  const [showQuizEdit, setShowQuizEdit] = useState(false);
  const [showQuizTake, setShowQuizTake] = useState(false);
  const [showQuizResults, setShowQuizResults] = useState(false);
  const [showQuestionManage, setShowQuestionManage] = useState(false);
  const [showQuestionCreate, setShowQuestionCreate] = useState(false);
  const [showQuestionEdit, setShowQuestionEdit] = useState(false);
  const [showCertificateIssue, setShowCertificateIssue] = useState(false);
  const [showCertificateDetail, setShowCertificateDetail] = useState(false);
  const [showSkillCreate, setShowSkillCreate] = useState(false);
  const [showSkillEdit, setShowSkillEdit] = useState(false);
  const [showSkillDetail, setShowSkillDetail] = useState(false);
  const [showUsersWithSkill, setShowUsersWithSkill] = useState(false);
  const [showUserSkillAdd, setShowUserSkillAdd] = useState(false);
  const [showUserSkillEdit, setShowUserSkillEdit] = useState(false);
  const [showSkillGap, setShowSkillGap] = useState(false);
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const [showAllUserSkills, setShowAllUserSkills] = useState(false);
  
  const [newCourse, setNewCourse] = useState({
    title: "",
    description: "",
    category: "",
    level: "",
    duration_hours: "",
    learning_objectives: "",
    is_mandatory: false,
  });

  const [editCourse, setEditCourse] = useState({
    id: null,
    title: "",
    description: "",
    category: "",
    level: "",
    instructor: null,
    duration_hours: "",
    prerequisites: "",
    learning_objectives: "",
    is_mandatory: false,
    status: "",
    max_enrollments: "",
    enrollment_deadline: "",
    start_date: "",
    end_date: "",
  });

  const [newModule, setNewModule] = useState({
    course: null,
    title: "",
    description: "",
    content_type: "",
    order: "",
    content: "",
    duration_minutes: "",
    is_mandatory: false,
    is_published: false,
  });

  const [editModule, setEditModule] = useState({
    id: null,
    course: null,
    title: "",
    description: "",
    content_type: "",
    order: "",
    content: "",
    duration_minutes: "",
    is_mandatory: false,
    is_published: false,
  });

  const [selectedModuleDetail, setSelectedModuleDetail] = useState(null);
  const [allModules, setAllModules] = useState([]);
  const [allEnrollments, setAllEnrollments] = useState([]);
  const [selectedEnrollmentDetail, setSelectedEnrollmentDetail] = useState(null);
  const [allProgress, setAllProgress] = useState([]);

  const [newEnrollment, setNewEnrollment] = useState({
    user: null,
    course: null,
    deadline: "",
    status: "active",
  });

  const [editEnrollment, setEditEnrollment] = useState({
    id: null,
    user: null,
    course: null,
    status: "",
    deadline: "",
    final_score: "",
  });

  const [newQuiz, setNewQuiz] = useState({
    course: null,
    module: null,
    title: "",
    description: "",
    difficulty: "",
    time_limit_minutes: "",
    passing_score: "",
    max_attempts: "",
    is_mandatory: false,
    randomize_questions: false,
    show_correct_answers: true,
  });

  const [editQuiz, setEditQuiz] = useState({
    id: null,
    course: null,
    module: null,
    title: "",
    description: "",
    difficulty: "",
    time_limit_minutes: "",
    passing_score: "",
    max_attempts: "",
    is_mandatory: false,
    randomize_questions: false,
    show_correct_answers: true,
  });

  const [newQuestion, setNewQuestion] = useState({
    quiz: null,
    order: "",
    question_type: "",
    question_text: "",
    options: [],
    correct_answer: [],
    points: "",
    explanation: ""
  });

  const [editQuestion, setEditQuestion] = useState({
    id: null,
    quiz: null,
    order: "",
    question_type: "",
    question_text: "",
    options: [],
    correct_answer: [],
    points: "",
    explanation: ""
  });

  const [newCertificate, setNewCertificate] = useState({
    user: null,
    course: null,
    enrollment: null,
    completion_score: "",
    quiz_average: "",
    expiry_date: "",
  });

  const [newSkill, setNewSkill] = useState({
    name: "",
    category: "",
    description: "",
    related_courses: [],
  });

  const [editSkill, setEditSkill] = useState({
    id: null,
    name: "",
    category: "",
    description: "",
    related_courses: [],
  });

  const [selectedSkillDetail, setSelectedSkillDetail] = useState(null);
  const [usersWithSkill, setUsersWithSkill] = useState([]);
  const [allUserSkills, setAllUserSkills] = useState([]);

  const [newUserSkill, setNewUserSkill] = useState({
    skill: null,
    proficiency_level: "",
    years_of_experience: "",
    notes: "",
  });

  const [editUserSkill, setEditUserSkill] = useState({
    id: null,
    skill: null,
    proficiency_level: "",
    years_of_experience: "",
    notes: "",
  });

  /* ================= COURSES ================= */
  const loadCourses = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/courses/`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      const coursesArray = Array.isArray(data) ? data : data.results || [];
      setCourses(coursesArray);
    } catch (err) {
      console.error('Load courses error:', err);
      setError("Failed to load courses");
    } finally {
      setLoading(false);
    }
  };

  // API #3: Get course details with modules
  const viewCourseDetails = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/courses/${id}/`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      if (res.ok) {
        setSelectedCourse(data);
        setModules(data.modules || []);
        setShowCourseDetail(true);
      }
    } catch (err) {
      setError("Failed to load course details");
    }
  };

  // API #10: Get course statistics
  const viewCourseStats = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/courses/${id}/statistics/`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      if (res.ok) {
        setCourseStats(data);
        setShowStats(true);
      }
    } catch (err) {
      setError("Failed to load statistics");
    }
  };

  const publishCourse = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/courses/${id}/publish/`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error();
      loadCourses();
    } catch {
      setError("Publish failed");
    }
  };

  const createCourse = async () => {
    try {
      console.log('Creating course with data:', newCourse);
      const res = await fetch(`${API_BASE}/courses/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(newCourse),
      });
      console.log('Create course response status:', res.status);
      const data = await res.json();
      console.log('Create course response data:', data);
      
      if (!res.ok) {
        setError(JSON.stringify(data) || "Course creation failed");
        return;
      }
      
      setShowCreate(false);
      setNewCourse({ 
        title: "", 
        description: "",
        category: "", 
        level: "", 
        duration_hours: "",
        learning_objectives: "",
        is_mandatory: false 
      });
      loadCourses();
    } catch (err) {
      console.error('Create course error:', err);
      setError("Course creation failed: " + err.message);
    }
  };

  // API #4 & #5: Update course (PUT/PATCH)
  const updateCourse = async () => {
    try {
      const res = await fetch(`${API_BASE}/courses/${editCourse.id}/`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(editCourse),
      });
      const data = await res.json();
      
      if (!res.ok) {
        setError(JSON.stringify(data) || "Course update failed");
        return;
      }
      
      setShowCourseEdit(false);
      setEditCourse({
        id: null,
        title: "",
        description: "",
        category: "",
        level: "",
        instructor: null,
        duration_hours: "",
        prerequisites: "",
        learning_objectives: "",
        is_mandatory: false,
        status: "",
        max_enrollments: "",
        enrollment_deadline: "",
        start_date: "",
        end_date: "",
      });
      loadCourses();
    } catch (err) {
      setError("Course update failed: " + err.message);
    }
  };

  // API #6: Delete course
  const deleteCourse = async (courseId) => {
    if (!window.confirm('Delete this course? This will remove all enrollments and progress.')) return;
    
    try {
      const res = await fetch(`${API_BASE}/courses/${courseId}/`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      
      if (res.ok) {
        alert('Course deleted successfully');
        loadCourses();
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to delete course");
      }
    } catch (err) {
      setError("Failed to delete course: " + err.message);
    }
  };

  // API #7: List modules for a course
  const loadCourseModules = async (courseId) => {
    try {
      const res = await fetch(`${API_BASE}/courses/${courseId}/modules/`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      setModules(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError("Failed to load course modules");
    }
  };

  // API #9: Archive course
  const archiveCourse = async (courseId) => {
    if (!window.confirm('Archive this course? It will no longer be available for new enrollments.')) return;
    
    try {
      const res = await fetch(`${API_BASE}/courses/${courseId}/archive/`, {
        method: 'POST',
        headers: authHeaders()
      });
      
      if (res.ok) {
        alert('Course archived successfully');
        loadCourses();
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to archive course");
      }
    } catch (err) {
      setError("Failed to archive course: " + err.message);
    }
  };

  /* ================= MODULES ================= */
  // API #12: Create module
  const createModule = async () => {
    try {
      const res = await fetch(`${API_BASE}/modules/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(newModule),
      });
      const data = await res.json();
      
      if (!res.ok) {
        setError(JSON.stringify(data) || "Module creation failed");
        return;
      }
      
      setShowModuleCreate(false);
      setNewModule({
        course: null,
        title: "",
        description: "",
        content_type: "",
        order: "",
        content: "",
        duration_minutes: "",
        is_mandatory: false,
        is_published: false,
      });
      
      if (selectedCourse) {
        viewCourseDetails(selectedCourse.id);
      }
    } catch (err) {
      setError("Module creation failed: " + err.message);
    }
  };

  // API #16: Delete module
  const deleteModule = async (moduleId) => {
    if (!window.confirm('Delete this module?')) return;
    
    try {
      const res = await fetch(`${API_BASE}/modules/${moduleId}/`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      
      if (res.ok && selectedCourse) {
        viewCourseDetails(selectedCourse.id);
      }
    } catch (err) {
      setError("Failed to delete module");
    }
  };

  // API #11: List all modules
  const loadAllModules = async (courseFilter = null) => {
    try {
      const url = courseFilter 
        ? `${API_BASE}/modules/?course=${courseFilter}`
        : `${API_BASE}/modules/`;
      const res = await fetch(url, { headers: authHeaders() });
      const data = await res.json();
      setAllModules(Array.isArray(data) ? data : data.results || []);
      setShowAllModules(true);
    } catch (err) {
      setError("Failed to load modules");
    }
  };

  // API #13: Get module details
  const viewModuleDetails = async (moduleId) => {
    try {
      const res = await fetch(`${API_BASE}/modules/${moduleId}/`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      if (res.ok) {
        setSelectedModuleDetail(data);
        setShowModuleDetail(true);
      }
    } catch (err) {
      setError("Failed to load module details");
    }
  };

  // API #14 & #15: Update module (PUT/PATCH)
  const updateModule = async () => {
    try {
      const res = await fetch(`${API_BASE}/modules/${editModule.id}/`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(editModule),
      });
      const data = await res.json();
      
      if (!res.ok) {
        setError(JSON.stringify(data) || "Module update failed");
        return;
      }
      
      setShowModuleEdit(false);
      setEditModule({
        id: null,
        course: null,
        title: "",
        description: "",
        content_type: "",
        order: "",
        content: "",
        duration_minutes: "",
        is_mandatory: false,
        is_published: false,
      });
      
      if (selectedCourse) {
        viewCourseDetails(selectedCourse.id);
      }
      if (showAllModules) {
        loadAllModules();
      }
    } catch (err) {
      setError("Module update failed: " + err.message);
    }
  };

  /* ================= ENROLLMENTS ================= */
  const selfEnroll = async (courseId) => {
    if (role !== "employee") return;
    try {
      const res = await fetch(`${API_BASE}/enrollments/enroll/`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ course: courseId }),
      });
      
      const data = await res.json();
      console.log('Enroll response:', res.status, data);
      
      if (!res.ok) {
        // Extract error message from various DRF error formats
        let errorMsg = "Enrollment failed";
        
        if (data.detail) {
          errorMsg = data.detail;
        } else if (data.error) {
          errorMsg = data.error;
        } else if (data.non_field_errors && data.non_field_errors.length > 0) {
          errorMsg = data.non_field_errors[0];
        } else if (data.course && Array.isArray(data.course) && data.course.length > 0) {
          // Handle field-specific errors like {"course": ["error message"]}
          errorMsg = data.course[0];
        } else {
          // Check for any field-level error arrays
          const fieldErrors = Object.entries(data)
            .filter(([key, val]) => Array.isArray(val) && val.length > 0)
            .map(([key, val]) => val[0]);
          
          if (fieldErrors.length > 0) {
            errorMsg = fieldErrors[0];
          } else {
            errorMsg = JSON.stringify(data);
          }
        }
        
        console.error('Enrollment error:', errorMsg);
        setError(errorMsg);
        return;
      }
      
      // Show success message
      alert('Successfully enrolled in course!');
      
      // Reload both courses and my courses to update UI
      await loadMyCourses();
      await loadCourses();
    } catch (err) {
      console.error('Enrollment error:', err);
      setError("Enrollment failed: " + err.message);
    }
  };

  const loadMyCourses = async () => {
    if (role !== "employee") return;
    try {
      const res = await fetch(`${API_BASE}/enrollments/my_courses/`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      const myCoursesArray = Array.isArray(data) ? data : data.results || [];
      setMyCourses(myCoursesArray);
    } catch (err) {
      console.error('Load my courses error:', err);
      setError("Failed to load my courses");
    }
  };

  // API #24: Drop enrollment
  const dropEnrollment = async (enrollmentId) => {
    if (!window.confirm('Drop this enrollment?')) return;
    
    try {
      const res = await fetch(`${API_BASE}/enrollments/${enrollmentId}/drop/`, {
        method: 'POST',
        headers: authHeaders()
      });
      
      const data = await res.json();
      
      if (res.ok) {
        alert('Successfully dropped from course');
        // Reload both courses and my courses to update UI
        await loadMyCourses();
        await loadCourses();
      } else {
        setError(data.detail || JSON.stringify(data) || "Failed to drop enrollment");
      }
    } catch (err) {
      setError("Failed to drop enrollment: " + err.message);
    }
  };

  // API #17: List all enrollments (Admin/Manager)
  const loadAllEnrollments = async (filters = {}) => {
    try {
      const params = new URLSearchParams(filters);
      const url = params.toString() 
        ? `${API_BASE}/enrollments/?${params}` 
        : `${API_BASE}/enrollments/`;
      const res = await fetch(url, { headers: authHeaders() });
      const data = await res.json();
      setAllEnrollments(Array.isArray(data) ? data : data.results || []);
      setShowAllEnrollments(true);
    } catch (err) {
      setError("Failed to load enrollments");
    }
  };

  // API #18: Create enrollment (Admin/HR)
  const createEnrollment = async () => {
    try {
      const res = await fetch(`${API_BASE}/enrollments/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(newEnrollment),
      });
      const data = await res.json();
      
      if (!res.ok) {
        setError(JSON.stringify(data) || "Enrollment creation failed");
        return;
      }
      
      setShowEnrollmentCreate(false);
      setNewEnrollment({
        user: null,
        course: null,
        deadline: "",
        status: "active",
      });
      loadAllEnrollments();
    } catch (err) {
      setError("Enrollment creation failed: " + err.message);
    }
  };

  // API #19: Get enrollment details
  const viewEnrollmentDetails = async (enrollmentId) => {
    try {
      const res = await fetch(`${API_BASE}/enrollments/${enrollmentId}/`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      if (res.ok) {
        setSelectedEnrollmentDetail(data);
        setShowEnrollmentDetail(true);
      }
    } catch (err) {
      setError("Failed to load enrollment details");
    }
  };

  // API #20 & #21: Update enrollment (PUT/PATCH)
  const updateEnrollment = async () => {
    try {
      const res = await fetch(`${API_BASE}/enrollments/${editEnrollment.id}/`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(editEnrollment),
      });
      const data = await res.json();
      
      if (!res.ok) {
        setError(JSON.stringify(data) || "Enrollment update failed");
        return;
      }
      
      setShowEnrollmentEdit(false);
      setEditEnrollment({
        id: null,
        user: null,
        course: null,
        status: "",
        deadline: "",
        final_score: "",
      });
      loadAllEnrollments();
    } catch (err) {
      setError("Enrollment update failed: " + err.message);
    }
  };

  /* ================= PROGRESS ================= */
  // API #29: Get my progress
  const loadMyProgress = async () => {
    if (role !== "employee") return;
    
    try {
      const res = await fetch(`${API_BASE}/progress/my_progress/`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      const progressArray = Array.isArray(data) ? data : data.results || [];
      setMyProgress(progressArray);
      setShowProgress(true);
    } catch (err) {
      setError("Failed to load progress");
    }
  };

  // API #28: Update module progress
  const updateProgress = async (moduleId, status, timeSpent) => {
    try {
      const res = await fetch(`${API_BASE}/progress/update_progress/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({
          module_id: moduleId,
          status: status,
          time_spent_minutes: timeSpent
        })
      });
      
      if (res.ok) {
        // Reload both progress and my courses to update UI
        await loadMyProgress();
        await loadMyCourses();
      }
    } catch (err) {
      setError("Failed to update progress");
    }
  };

  // API #27: List all progress (Admin view)
  const loadAllProgress = async (enrollmentFilter = null) => {
    try {
      const url = enrollmentFilter 
        ? `${API_BASE}/progress/?enrollment=${enrollmentFilter}`
        : `${API_BASE}/progress/`;
      const res = await fetch(url, { headers: authHeaders() });
      const data = await res.json();
      setAllProgress(Array.isArray(data) ? data : data.results || []);
      setShowAllProgress(true);
    } catch (err) {
      setError("Failed to load progress");
    }
  };

  /* ================= APPROVALS ================= */
  const loadPending = async () => {
    if (!["manager", "hr", "admin"].includes(role)) return;
    try {
      const res = await fetch(`${API_BASE}/enrollments/pending/`, {
        headers: authHeaders(),
      });
      const data = await res.json();
      const pendingArray = Array.isArray(data) ? data : data.results || [];
      setPending(pendingArray);
    } catch (err) {
      console.error('Load pending error:', err);
      setError("Failed to load approvals");
    }
  };

  /* ================= DAY 21: QUIZZES ================= */
  // API #1-3: Get quizzes with filters
  const loadQuizzes = async (filters = {}) => {
    try {
      setLoading(true);
      const params = new URLSearchParams(filters);
      const url = params.toString() ? `${API_BASE}/quizzes/?${params}` : `${API_BASE}/quizzes/`;
      const res = await fetch(url, { headers: authHeaders() });
      const data = await res.json();
      setQuizzes(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError("Failed to load quizzes");
    } finally {
      setLoading(false);
    }
  };

  // API #4: Get quiz details with questions
  const getQuizDetails = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/quizzes/${id}/`, { headers: authHeaders() });
      const data = await res.json();
      if (res.ok) {
        setSelectedQuiz(data);
        setShowQuizTake(true);
      }
    } catch (err) {
      setError("Failed to load quiz");
    }
  };

  // API #5: Create quiz (Admin/HR)
  const createQuiz = async () => {
    try {
      const res = await fetch(`${API_BASE}/quizzes/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(newQuiz)
      });
      const data = await res.json();
      if (res.ok) {
        setShowQuizCreate(false);
        loadQuizzes();
        setNewQuiz({
          course: null, module: null, title: "", description: "",
          difficulty: "", time_limit_minutes: "", passing_score: "",
          max_attempts: "", is_mandatory: false, randomize_questions: false,
          show_correct_answers: true
        });
      } else {
        setError(JSON.stringify(data));
      }
    } catch (err) {
      setError("Failed to create quiz");
    }
  };

  // API #6: Update quiz (Admin/HR)
  const updateQuiz = async () => {
    try {
      const res = await fetch(`${API_BASE}/quizzes/${editQuiz.id}/`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(editQuiz)
      });
      const data = await res.json();
      if (res.ok) {
        setShowQuizEdit(false);
        loadQuizzes();
        alert('Quiz updated successfully');
      } else {
        setError(JSON.stringify(data));
      }
    } catch (err) {
      setError("Failed to update quiz");
    }
  };

  // API #7: Delete quiz (Admin/HR)
  const deleteQuiz = async (id) => {
    if (!window.confirm('Delete this quiz?')) return;
    try {
      const res = await fetch(`${API_BASE}/quizzes/${id}/`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      if (res.ok) loadQuizzes();
    } catch (err) {
      setError("Failed to delete quiz");
    }
  };

  // API #8: Start quiz attempt
  const startQuizAttempt = async (quizId) => {
    try {
      // Reset quiz answers state
      setQuizAnswers({});
      
      const res = await fetch(`${API_BASE}/quizzes/${quizId}/start_attempt/`, {
        method: 'POST',
        headers: authHeaders()
      });
      const data = await res.json();
      if (res.ok) {
        setCurrentAttempt(data);
        // Load quiz details after successful attempt start
        getQuizDetails(quizId);
      } else {
        setError(data.detail || data.error || JSON.stringify(data));
      }
    } catch (err) {
      setError("Failed to start attempt");
    }
  };

  // API #9: Submit quiz answers
  const submitQuiz = async (quizId) => {
    try {
      const res = await fetch(`${API_BASE}/quizzes/${quizId}/submit/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ answers: quizAnswers })
      });
      const data = await res.json();
      if (res.ok) {
        setShowQuizTake(false);
        setShowQuizResults(true);
        setCurrentAttempt(data);
        setQuizAnswers({}); // Reset answers after submission
        loadMyAttempts();
      } else {
        setError(data.detail || data.error || JSON.stringify(data));
      }
    } catch (err) {
      setError("Failed to submit quiz");
    }
  };

  // API #10: Get my attempts
  const loadMyAttempts = async (quizId = null) => {
    if (role !== 'employee') return;
    try {
      const url = quizId ? `${API_BASE}/quizzes/my_attempts/?quiz=${quizId}` : `${API_BASE}/quizzes/my_attempts/`;
      const res = await fetch(url, { headers: authHeaders() });
      const data = await res.json();
      setQuizAttempts(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError("Failed to load attempts");
    }
  };

  // API #11: Get leaderboard
  const loadLeaderboard = async (quizId) => {
    try {
      const res = await fetch(`${API_BASE}/quizzes/${quizId}/leaderboard/`, { headers: authHeaders() });
      const data = await res.json();
      if (res.ok) setLeaderboard(data);
    } catch (err) {
      setError("Failed to load leaderboard");
    }
  };

  /* ================= QUIZ QUESTIONS ================= */
  // API #12: Get quiz questions
  const loadQuizQuestions = async (quizId) => {
    try {
      const res = await fetch(`${API_BASE}/quiz-questions/?quiz=${quizId}`, { headers: authHeaders() });
      const data = await res.json();
      setQuizQuestions(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError("Failed to load questions");
    }
  };

  // API #13: Create question
  const createQuestion = async () => {
    try {
      const payload = {
        ...newQuestion,
        options: newQuestion.options.filter(Boolean),
        correct_answer: newQuestion.correct_answer.filter(Boolean)
      };
      
      const res = await fetch(`${API_BASE}/quiz-questions/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        setShowQuestionCreate(false);
        loadQuizQuestions(newQuestion.quiz);
        setNewQuestion({
          quiz: null, order: "", question_type: "", question_text: "",
          options: [], correct_answer: [], points: "", explanation: ""
        });
        alert('Question created successfully');
      } else {
        setError(JSON.stringify(data));
      }
    } catch (err) {
      setError("Failed to create question");
    }
  };

  // API #14: Update question
  const updateQuestion = async () => {
    try {
      const payload = {
        quiz: editQuestion.quiz,
        order: editQuestion.order,
        question_type: editQuestion.question_type,
        question_text: editQuestion.question_text,
        options: editQuestion.options.filter(Boolean),
        correct_answer: editQuestion.correct_answer.filter(Boolean),
        points: editQuestion.points,
        explanation: editQuestion.explanation
      };
      
      const res = await fetch(`${API_BASE}/quiz-questions/${editQuestion.id}/`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        setShowQuestionEdit(false);
        loadQuizQuestions(editQuestion.quiz);
        alert('Question updated successfully');
      } else {
        setError(JSON.stringify(data));
      }
    } catch (err) {
      setError("Failed to update question");
    }
  };

  // API #15: Delete question
  const deleteQuestion = async (id, quizId) => {
    if (!window.confirm('Delete this question?')) return;
    try {
      const res = await fetch(`${API_BASE}/quiz-questions/${id}/`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      if (res.ok) {
        loadQuizQuestions(quizId);
        alert('Question deleted successfully');
      }
    } catch (err) {
      setError("Failed to delete question");
    }
  };

  /* ================= DAY 21: CERTIFICATES ================= */
  // API #16-18: Get certificates with filters
  const loadAllCertificates = async (filters = {}) => {
    try {
      const params = new URLSearchParams(filters);
      const url = params.toString() ? `${API_BASE}/certificates/?${params}` : `${API_BASE}/certificates/`;
      const res = await fetch(url, { headers: authHeaders() });
      const data = await res.json();
      setCertificates(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError("Failed to load certificates");
    }
  };

  // API #19: Get my certificates
  const loadMyCertificates = async () => {
    try {
      const res = await fetch(`${API_BASE}/certificates/my_certificates/`, { headers: authHeaders() });
      const data = await res.json();
      setMyCertificates(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError("Failed to load certificates");
    }
  };

  // API #20: Get certificate details
  const getCertificateDetails = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/certificates/${id}/`, { headers: authHeaders() });
      const data = await res.json();
      if (res.ok) {
        setSelectedCertificate(data);
        setShowCertificateDetail(true);
      }
    } catch (err) {
      setError("Failed to load certificate");
    }
  };

  // API #22: Issue certificate (Admin/HR)
  const issueCertificate = async () => {
    try {
      const res = await fetch(`${API_BASE}/certificates/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(newCertificate)
      });
      const data = await res.json();
      if (res.ok) {
        setShowCertificateIssue(false);
        loadAllCertificates();
        setNewCertificate({
          user: null, course: null, enrollment: null,
          completion_score: "", quiz_average: "", expiry_date: ""
        });
      } else {
        setError(JSON.stringify(data));
      }
    } catch (err) {
      setError("Failed to issue certificate");
    }
  };

  // API #23: Revoke certificate (Admin/HR)
  const revokeCertificate = async (id) => {
    if (!window.confirm('Revoke this certificate?')) return;
    try {
      const res = await fetch(`${API_BASE}/certificates/${id}/revoke/`, {
        method: 'POST',
        headers: authHeaders()
      });
      if (res.ok) loadAllCertificates();
    } catch (err) {
      setError("Failed to revoke certificate");
    }
  };

  // API #24: Reactivate certificate (Admin/HR)
  const reactivateCertificate = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/certificates/${id}/reactivate/`, {
        method: 'POST',
        headers: authHeaders()
      });
      if (res.ok) loadAllCertificates();
    } catch (err) {
      setError("Failed to reactivate certificate");
    }
  };

  /* ================= DAY 21: SKILLS ================= */
  // API #25-27: Get skills with filters
  const loadSkills = async (filters = {}) => {
    try {
      const params = new URLSearchParams(filters);
      const url = params.toString() ? `${API_BASE}/skills/?${params}` : `${API_BASE}/skills/`;
      const res = await fetch(url, { headers: authHeaders() });
      const data = await res.json();
      setSkills(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError("Failed to load skills");
    }
  };

  // API #30: Create skill (Admin/HR)
  const createSkill = async () => {
    try {
      const res = await fetch(`${API_BASE}/skills/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(newSkill)
      });
      const data = await res.json();
      if (res.ok) {
        setShowSkillCreate(false);
        loadSkills();
        setNewSkill({ name: "", category: "", description: "", related_courses: [] });
      } else {
        setError(JSON.stringify(data));
      }
    } catch (err) {
      setError("Failed to create skill");
    }
  };

  // API #31: Update skill (Admin/HR)
  const updateSkill = async () => {
    try {
      const res = await fetch(`${API_BASE}/skills/${editSkill.id}/`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(editSkill)
      });
      const data = await res.json();
      if (res.ok) {
        setShowSkillEdit(false);
        loadSkills();
        alert('Skill updated successfully');
      } else {
        setError(JSON.stringify(data));
      }
    } catch (err) {
      setError("Failed to update skill");
    }
  };

  // API #28: Get skill details
  const loadSkillDetails = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/skills/${id}/`, { headers: authHeaders() });
      const data = await res.json();
      if (res.ok) {
        setSelectedSkillDetail(data);
        setShowSkillDetail(true);
      }
    } catch (err) {
      setError("Failed to load skill details");
    }
  };

  // API #29: Get users with skill
  const loadUsersWithSkill = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/skills/${id}/users_with_skill/`, { headers: authHeaders() });
      const data = await res.json();
      if (res.ok) {
        setUsersWithSkill(Array.isArray(data) ? data : data.results || []);
        setShowUsersWithSkill(true);
      }
    } catch (err) {
      setError("Failed to load users");
    }
  };

  // API #32: Delete skill (Admin/HR)
  const deleteSkill = async (id) => {
    if (!window.confirm('Delete this skill?')) return;
    try {
      const res = await fetch(`${API_BASE}/skills/${id}/`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      if (res.ok) loadSkills();
    } catch (err) {
      setError("Failed to delete skill");
    }
  };

  // API #34: Get my skills
  const loadMySkills = async () => {
    if (role !== 'employee') return;
    try {
      const res = await fetch(`${API_BASE}/user-skills/my_skills/`, { headers: authHeaders() });
      const data = await res.json();
      setMySkills(Array.isArray(data) ? data : data.results || []);
    } catch (err) {
      setError("Failed to load skills");
    }
  };

  // API #35: Skill gap analysis
  const loadSkillGapAnalysis = async () => {
    if (role !== 'employee') return;
    try {
      const res = await fetch(`${API_BASE}/user-skills/skill_gap_analysis/`, { headers: authHeaders() });
      const data = await res.json();
      if (res.ok) {
        setSkillGapAnalysis(data);
        setShowSkillGap(true);
      }
    } catch (err) {
      setError("Failed to load analysis");
    }
  };

  // API #36: Add user skill
  const addUserSkill = async () => {
    try {
      // Include user ID in the payload
      const payload = {
        ...newUserSkill,
        user: user?.id
      };
      
      const res = await fetch(`${API_BASE}/user-skills/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        setShowUserSkillAdd(false);
        loadMySkills();
        setNewUserSkill({ skill: null, proficiency_level: "", years_of_experience: "", notes: "" });
      } else {
        setError(JSON.stringify(data));
      }
    } catch (err) {
      setError("Failed to add skill");
    }
  };

  // API #37: Update user skill
  const updateUserSkill = async () => {
    try {
      const payload = {
        skill: editUserSkill.skill,
        proficiency_level: editUserSkill.proficiency_level,
        years_of_experience: editUserSkill.years_of_experience,
        notes: editUserSkill.notes
      };
      
      const res = await fetch(`${API_BASE}/user-skills/${editUserSkill.id}/`, {
        method: 'PUT',
        headers: authHeaders(),
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        setShowUserSkillEdit(false);
        loadMySkills();
        alert('Skill updated successfully');
      } else {
        setError(JSON.stringify(data));
      }
    } catch (err) {
      setError("Failed to update skill");
    }
  };

  // API #33: Get all user skills (Admin/HR)
  const loadAllUserSkills = async () => {
    if (role !== 'admin' && role !== 'hr') return;
    try {
      const res = await fetch(`${API_BASE}/user-skills/`, { headers: authHeaders() });
      const data = await res.json();
      setAllUserSkills(Array.isArray(data) ? data : data.results || []);
      setShowAllUserSkills(true);
    } catch (err) {
      setError("Failed to load all user skills");
    }
  };

  // API #38: Remove user skill
  const removeUserSkill = async (id) => {
    if (!window.confirm('Remove this skill?')) return;
    try {
      const res = await fetch(`${API_BASE}/user-skills/${id}/`, {
        method: 'DELETE',
        headers: authHeaders()
      });
      if (res.ok) loadMySkills();
    } catch (err) {
      setError("Failed to remove skill");
    }
  };

  // API #39: Endorse skill
  const endorseSkill = async (userSkillId, comment) => {
    try {
      const res = await fetch(`${API_BASE}/user-skills/${userSkillId}/endorse/`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ comment })
      });
      if (res.ok) {
        alert('Endorsement added!');
      } else {
        const data = await res.json();
        setError(data.detail || "Failed to endorse");
      }
    } catch (err) {
      setError("Failed to endorse");
    }
  };

  /* ================= LOAD DATA ================= */
  useEffect(() => {
    if (activeTab === 'courses') {
      loadCourses();
      loadMyCourses();
      if (["manager", "hr", "admin"].includes(role)) {
        loadPending();
      }
    } else if (activeTab === 'quizzes') {
      loadQuizzes();
      if (role === 'employee') loadMyAttempts();
    } else if (activeTab === 'certificates') {
      if (role === 'employee') {
        loadMyCertificates();
      } else {
        loadAllCertificates();
      }
    } else if (activeTab === 'skills') {
      loadSkills();
      if (role === 'employee') {
        loadMySkills();
      }
    }
  }, [role, activeTab]);

  const approveEnrollment = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/enrollments/${id}/approve/`, {
        method: "POST",
        headers: authHeaders(),
      });
      if (!res.ok) throw new Error();
      loadPending();
    } catch {
      setError("Approval failed");
    }
  };

  if (loading) {
    return <div className="p-4"><h3>Loading LMS...</h3></div>;
  }

  return (
    <div className="p-4">
      <h3>📚 Learning Management System</h3>

      {error && <Alert variant="danger" onClose={() => setError("")} dismissible>{error}</Alert>}

      {/* Tab Navigation */}
      <div className="btn-group mb-3" role="group">
        <button 
          className={`btn ${activeTab === 'courses' ? 'btn-primary' : 'btn-outline-primary'}`}
          onClick={() => setActiveTab('courses')}
        >
          📖 Courses
        </button>
        <button 
          className={`btn ${activeTab === 'quizzes' ? 'btn-primary' : 'btn-outline-primary'}`}
          onClick={() => setActiveTab('quizzes')}
        >
          📝 Quizzes
        </button>
        <button 
          className={`btn ${activeTab === 'certificates' ? 'btn-primary' : 'btn-outline-primary'}`}
          onClick={() => setActiveTab('certificates')}
        >
          🎓 Certificates
        </button>
        <button 
          className={`btn ${activeTab === 'skills' ? 'btn-primary' : 'btn-outline-primary'}`}
          onClick={() => setActiveTab('skills')}
        >
          💡 Skills
        </button>
      </div>

      {/* ============== COURSES TAB ============== */}
      {activeTab === 'courses' && (
        <>
          {/* ========== ADMIN / HR CREATE COURSE ========== */}
          {(role === "admin" || role === "hr") && (
            <div className="mb-3 d-flex gap-2 flex-wrap">
              <Button onClick={() => setShowCreate(true)}>
                + Create Course
              </Button>
              <Button variant="outline-primary" onClick={() => loadAllModules()}>
                View All Modules
              </Button>
              <Button variant="outline-success" onClick={() => loadAllEnrollments()}>
                View All Enrollments
              </Button>
              <Button variant="outline-info" onClick={() => loadAllProgress()}>
                View All Progress
              </Button>
            </div>
          )}

          {/* ========== COURSE LIST ========== */}
          <h5>Course Catalog</h5>
          <Table bordered hover size="sm">
            <thead>
              <tr>
                <th>Title</th>
                <th>Category</th>
                <th>Level</th>
                <th>Mandatory</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {courses.length === 0 && (
                <tr>
                  <td colSpan="5" className="text-center">No courses found</td>
                </tr>
              )}
              {courses.map((c) => {
                const isEnrolled = myCourses.some(enrolled => enrolled.course === c.id);
            
            return (
            <tr key={c.id}>
              <td>
                <a href="#" onClick={(e) => { e.preventDefault(); viewCourseDetails(c.id); }}>
                  {c.title}
                </a>
              </td>
              <td>{c.category}</td>
              <td>{c.level}</td>
              <td>{c.is_mandatory ? "Yes" : "No"}</td>
              <td>
                <div className="d-flex gap-1 flex-wrap">
                  {role === "employee" && (
                    isEnrolled ? (
                      <Badge bg="success">Enrolled</Badge>
                    ) : (
                      <Button size="sm" variant="success" onClick={() => selfEnroll(c.id)}>
                        Enroll
                      </Button>
                    )
                  )}

                  {(role === "admin" || role === "hr") && (
                    <>
                      {c.status === "draft" && (
                        <Button size="sm" variant="warning" onClick={() => publishCourse(c.id)}>
                          Publish
                        </Button>
                      )}
                      {c.status === "published" && (
                        <Button size="sm" variant="secondary" onClick={() => archiveCourse(c.id)}>
                          Archive
                        </Button>
                      )}
                      <Button size="sm" variant="primary" onClick={() => {
                        setEditCourse({
                          id: c.id,
                          title: c.title,
                          description: c.description || "",
                          category: c.category,
                          level: c.level,
                          instructor: c.instructor,
                          duration_hours: c.duration_hours,
                          prerequisites: c.prerequisites || "",
                          learning_objectives: c.learning_objectives || "",
                          is_mandatory: c.is_mandatory,
                          status: c.status,
                          max_enrollments: c.max_enrollments || "",
                          enrollment_deadline: c.enrollment_deadline || "",
                          start_date: c.start_date || "",
                          end_date: c.end_date || "",
                        });
                        setShowCourseEdit(true);
                      }}>
                        Edit
                      </Button>
                      <Button size="sm" variant="info" onClick={() => viewCourseStats(c.id)}>
                        Stats
                      </Button>
                      <Button size="sm" variant="danger" onClick={() => deleteCourse(c.id)}>
                        Delete
                      </Button>
                    </>
                  )}
                </div>
              </td>
            </tr>
            );
          })}
        </tbody>
      </Table>

      {/* ========== EMPLOYEE ONLY – MY COURSES ========== */}
      {role === "employee" && (
        <>
          <div className="d-flex justify-content-between align-items-center mt-4">
            <h5>My Courses</h5>
            <Button size="sm" variant="outline-primary" onClick={loadMyProgress}>
              View My Progress
            </Button>
          </div>
          <Table bordered size="sm">
            <thead>
              <tr>
                <th>Course</th>
                <th>Status</th>
                <th>Progress</th>
                <th>Deadline</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {myCourses.length === 0 && (
                <tr>
                  <td colSpan="5" className="text-center">No enrollments</td>
                </tr>
              )}
              {myCourses.map((c) => (
                <tr key={c.id}>
                  <td>{c.course_title}</td>
                  <td>
                    <Badge bg={c.status === 'completed' ? 'success' : c.status === 'pending' ? 'warning' : 'info'}>
                      {c.status}
                    </Badge>
                  </td>
                  <td>
                    <ProgressBar
                      now={parseFloat(c.progress_percentage)}
                      label={`${c.progress_percentage}%`}
                    />
                  </td>
                  <td>
                    {c.deadline}
                    {c.is_overdue && <Badge bg="danger" className="ms-2">Overdue</Badge>}
                  </td>
                  <td>
                    <Button size="sm" variant="danger" onClick={() => dropEnrollment(c.id)}>
                      Drop
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </>
      )}

      {/* ========== MANAGER / HR / ADMIN – APPROVALS ========== */}
      {["manager", "hr", "admin"].includes(role) && (
        <>
          <h5 className="mt-4">Pending Approvals</h5>
          <Table bordered size="sm">
            <thead>
              <tr>
                <th>Course</th>
                <th>User</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {pending.length === 0 && (
                <tr>
                  <td colSpan="3" className="text-center">No pending approvals</td>
                </tr>
              )}
              {pending.map((p) => (
                <tr key={p.id}>
                  <td>{p.course_title}</td>
                  <td>{p.user_name}</td>
                  <td>
                    <Button size="sm" onClick={() => approveEnrollment(p.id)}>
                      Approve
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </>
      )}
      </>
      )}

      {/* ============== QUIZZES TAB ============== */}
      {activeTab === 'quizzes' && (
        <>
          {(role === "admin" || role === "hr") && (
            <Button className="mb-3" onClick={() => setShowQuizCreate(true)}>
              + Create Quiz
            </Button>
          )}

          <h5>Quiz Catalog</h5>
          <Table bordered hover size="sm">
            <thead>
              <tr>
                <th>Title</th>
                <th>Course</th>
                <th>Difficulty</th>
                <th>Questions</th>
                <th>Passing Score</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {quizzes.length === 0 && (
                <tr>
                  <td colSpan="6" className="text-center">No quizzes found</td>
                </tr>
              )}
              {quizzes.map((q) => (
                <tr key={q.id}>
                  <td>{q.title}</td>
                  <td>{q.course_title || 'N/A'}</td>
                  <td><Badge bg={q.difficulty === 'easy' ? 'success' : q.difficulty === 'medium' ? 'warning' : 'danger'}>{q.difficulty}</Badge></td>
                  <td>{q.total_questions || 0}</td>
                  <td>{q.passing_score}%</td>
                  <td>
                    <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                      {role === 'employee' && (
                        <Button size="sm" variant="primary" onClick={() => {
                          setShowQuizResults(false); // Close results modal if open
                          startQuizAttempt(q.id);
                        }}>
                          Take Quiz
                        </Button>
                      )}
                      <Button size="sm" variant="info" onClick={() => {
                        loadLeaderboard(q.id);
                        setShowLeaderboard(true);
                      }}>
                        Leaderboard
                      </Button>
                      {(role === "admin" || role === "hr") && (
                        <>
                          <Button size="sm" variant="secondary" onClick={() => {
                            setSelectedQuizForQuestions(q);
                            loadQuizQuestions(q.id);
                            setShowQuestionManage(true);
                          }}>
                            Manage Questions
                          </Button>
                          <Button size="sm" variant="warning" onClick={() => {
                            setEditQuiz({
                              id: q.id,
                              course: q.course,
                              module: q.module,
                              title: q.title,
                              description: q.description,
                              difficulty: q.difficulty,
                              time_limit_minutes: q.time_limit_minutes,
                              passing_score: q.passing_score,
                              max_attempts: q.max_attempts,
                              is_mandatory: q.is_mandatory,
                              randomize_questions: q.randomize_questions,
                              show_correct_answers: q.show_correct_answers
                            });
                            setShowQuizEdit(true);
                          }}>
                            Edit
                          </Button>
                          <Button size="sm" variant="danger" onClick={() => deleteQuiz(q.id)}>
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

          {role === 'employee' && (
            <>
              <h5 className="mt-4">My Quiz Attempts</h5>
              <Table bordered size="sm">
                <thead>
                  <tr>
                    <th>Quiz</th>
                    <th>Attempt #</th>
                    <th>Score</th>
                    <th>Status</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {quizAttempts.length === 0 && (
                    <tr>
                      <td colSpan="5" className="text-center">No attempts yet</td>
                    </tr>
                  )}
                  {quizAttempts.map((a) => (
                    <tr key={a.id}>
                      <td>{a.quiz_title}</td>
                      <td>{a.attempt_number}</td>
                      <td>{a.score || 'N/A'}</td>
                      <td>
                        <Badge bg={a.passed ? 'success' : a.status === 'in_progress' ? 'warning' : 'danger'}>
                          {a.status}
                        </Badge>
                      </td>
                      <td>{new Date(a.submitted_at || a.started_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </>
          )}
        </>
      )}

      {/* ============== CERTIFICATES TAB ============== */}
      {activeTab === 'certificates' && (
        <>
          {(role === "admin" || role === "hr") && (
            <Button className="mb-3" onClick={() => setShowCertificateIssue(true)}>
              + Issue Certificate
            </Button>
          )}

          <h5>{role === 'employee' ? 'My Certificates' : 'All Certificates'}</h5>
          <Table bordered hover size="sm">
            <thead>
              <tr>
                <th>Certificate ID</th>
                <th>User</th>
                <th>Course</th>
                <th>Issued Date</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {(role === 'employee' ? myCertificates : certificates).length === 0 && (
                <tr>
                  <td colSpan="6" className="text-center">No certificates found</td>
                </tr>
              )}
              {(role === 'employee' ? myCertificates : certificates).map((cert) => (
                <tr key={cert.id}>
                  <td>{cert.certificate_id}</td>
                  <td>{cert.user_name}</td>
                  <td>{cert.course_title}</td>
                  <td>{new Date(cert.issued_date).toLocaleDateString()}</td>
                  <td>
                    <Badge bg={cert.status === 'active' ? 'success' : cert.status === 'expired' ? 'warning' : 'danger'}>
                      {cert.status}
                    </Badge>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                      <Button size="sm" variant="info" onClick={() => getCertificateDetails(cert.id)}>
                        View
                      </Button>
                      {(role === "admin" || role === "hr") && (
                        <>
                          {cert.status === 'active' && (
                            <Button size="sm" variant="warning" onClick={() => revokeCertificate(cert.id)}>
                              Revoke
                            </Button>
                          )}
                          {cert.status === 'revoked' && (
                            <Button size="sm" variant="success" onClick={() => reactivateCertificate(cert.id)}>
                              Reactivate
                            </Button>
                          )}
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </>
      )}

      {/* ============== SKILLS TAB ============== */}
      {activeTab === 'skills' && (
        <>
          {(role === "admin" || role === "hr") && (
            <Button className="mb-3" onClick={() => setShowSkillCreate(true)}>
              + Create Skill
            </Button>
          )}

          {role === 'employee' && (
            <div className="mb-3" style={{ display: 'flex', gap: '10px' }}>
              <Button variant="primary" onClick={() => setShowUserSkillAdd(true)}>
                + Add My Skill
              </Button>
              <Button variant="outline-info" onClick={loadSkillGapAnalysis}>
                View Skill Gap Analysis
              </Button>
            </div>
          )}

          {(role === 'admin' || role === 'hr') && (
            <Button className="mb-3" variant="outline-secondary" onClick={loadAllUserSkills}>
              View All User Skills
            </Button>
          )}

          {role === 'employee' && (
            <>
              <h5>My Skills</h5>
              <Table bordered size="sm" className="mb-4">
                <thead>
                  <tr>
                    <th>Skill</th>
                    <th>Category</th>
                    <th>Proficiency</th>
                    <th>Experience (years)</th>
                    <th>Endorsements</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {mySkills.length === 0 && (
                    <tr>
                      <td colSpan="6" className="text-center">No skills added yet</td>
                    </tr>
                  )}
                  {mySkills.map((us) => (
                    <tr key={us.id}>
                      <td>{us.skill_name}</td>
                      <td>{us.skill_category}</td>
                      <td>
                        <Badge bg={
                          us.proficiency_level === 'expert' ? 'success' :
                          us.proficiency_level === 'advanced' ? 'info' :
                          us.proficiency_level === 'intermediate' ? 'primary' : 'secondary'
                        }>
                          {us.proficiency_level}
                        </Badge>
                      </td>
                      <td>{us.years_of_experience}</td>
                      <td>{us.endorsement_count || 0}</td>
                      <td>
                        <Button size="sm" variant="warning" className="me-2" onClick={() => {
                          setEditUserSkill({
                            id: us.id,
                            skill: us.skill,
                            proficiency_level: us.proficiency_level,
                            years_of_experience: us.years_of_experience,
                            notes: us.notes || ""
                          });
                          setShowUserSkillEdit(true);
                        }}>
                          Edit
                        </Button>
                        <Button size="sm" variant="danger" onClick={() => removeUserSkill(us.id)}>
                          Remove
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </>
          )}

          <h5>All Skills</h5>
          <Table bordered hover size="sm">
            <thead>
              <tr>
                <th>Name</th>
                <th>Category</th>
                <th>Description</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {skills.length === 0 && (
                <tr>
                  <td colSpan="4" className="text-center">No skills found</td>
                </tr>
              )}
              {skills.map((sk) => (
                <tr key={sk.id}>
                  <td>{sk.name}</td>
                  <td><Badge>{sk.category}</Badge></td>
                  <td>{sk.description || 'N/A'}</td>
                  <td>
                    <Button size="sm" variant="info" className="me-2" onClick={() => loadSkillDetails(sk.id)}>
                      View
                    </Button>
                    <Button size="sm" variant="secondary" className="me-2" onClick={() => loadUsersWithSkill(sk.id)}>
                      Users
                    </Button>
                    {(role === "admin" || role === "hr") && (
                      <>
                        <Button size="sm" variant="warning" className="me-2" onClick={() => {
                          setEditSkill({
                            id: sk.id,
                            name: sk.name,
                            category: sk.category,
                            description: sk.description || "",
                            related_courses: sk.related_courses || []
                          });
                          setShowSkillEdit(true);
                        }}>
                          Edit
                        </Button>
                        <Button size="sm" variant="danger" onClick={() => deleteSkill(sk.id)}>
                          Delete
                        </Button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </>
      )}

      {/* ========== MODALS - COURSES ========== */}
      <Modal show={showCreate} onHide={() => setShowCreate(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Create Course</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <label className="form-label">Title *</label>
            <input
              className="form-control"
              placeholder="Course Title"
              value={newCourse.title}
              onChange={(e) => setNewCourse({ ...newCourse, title: e.target.value })}
            />
          </div>
          
          <div className="mb-3">
            <label className="form-label">Description *</label>
            <textarea
              className="form-control"
              placeholder="Course Description"
              rows="3"
              value={newCourse.description}
              onChange={(e) => setNewCourse({ ...newCourse, description: e.target.value })}
            />
          </div>
          
          <div className="mb-3">
            <label className="form-label">Category *</label>
            <select
              className="form-control"
              value={newCourse.category}
              onChange={(e) => setNewCourse({ ...newCourse, category: e.target.value })}
            >
              <option value="">Select Category</option>
              <option value="technical">Technical</option>
              <option value="leadership">Leadership</option>
              <option value="compliance">Compliance</option>
              <option value="soft_skills">Soft Skills</option>
              <option value="onboarding">Onboarding</option>
              <option value="professional">Professional</option>
            </select>
          </div>
          
          <div className="mb-3">
            <label className="form-label">Level *</label>
            <select
              className="form-control"
              value={newCourse.level}
              onChange={(e) => setNewCourse({ ...newCourse, level: e.target.value })}
            >
              <option value="">Select Level</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
          
          <div className="mb-3">
            <label className="form-label">Duration (hours) *</label>
            <input
              type="number"
              className="form-control"
              placeholder="e.g. 10"
              value={newCourse.duration_hours}
              onChange={(e) => setNewCourse({ ...newCourse, duration_hours: e.target.value })}
            />
          </div>
          
          <div className="mb-3">
            <label className="form-label">Learning Objectives *</label>
            <textarea
              className="form-control"
              placeholder="What will students learn?"
              rows="3"
              value={newCourse.learning_objectives}
              onChange={(e) => setNewCourse({ ...newCourse, learning_objectives: e.target.value })}
            />
          </div>
          
          <div className="mb-3">
            <label>
              <input
                type="checkbox"
                checked={newCourse.is_mandatory}
                onChange={(e) => setNewCourse({ ...newCourse, is_mandatory: e.target.checked })}
              /> Mandatory Course
            </label>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={createCourse}>Create</Button>
        </Modal.Footer>
      </Modal>

      {/* ========== COURSE DETAIL MODAL ========== */}
      <Modal show={showCourseDetail} onHide={() => setShowCourseDetail(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>{selectedCourse?.title}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedCourse && (
            <>
              <p><strong>Description:</strong> {selectedCourse.description}</p>
              <p><strong>Category:</strong> {selectedCourse.category}</p>
              <p><strong>Level:</strong> {selectedCourse.level}</p>
              <p><strong>Duration:</strong> {selectedCourse.duration_hours} hours</p>
              <p><strong>Learning Objectives:</strong> {selectedCourse.learning_objectives}</p>
              <p><strong>Status:</strong> <Badge bg="info">{selectedCourse.status}</Badge></p>
              
              <hr />
              <div className="d-flex justify-content-between align-items-center">
                <h5>Modules ({modules.length})</h5>
                {(role === "admin" || role === "hr") && (
                  <Button size="sm" onClick={() => {
                    setNewModule({...newModule, course: selectedCourse.id});
                    setShowModuleCreate(true);
                  }}>
                    + Add Module
                  </Button>
                )}
              </div>
              
              {modules.length === 0 ? (
                <p className="text-muted">No modules added yet</p>
              ) : (
                <Table bordered size="sm" className="mt-2">
                  <thead>
                    <tr>
                      <th>Order</th>
                      <th>Title</th>
                      <th>Type</th>
                      <th>Duration (min)</th>
                      <th>Status</th>
                      {(role === "admin" || role === "hr") && <th>Action</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {modules.map((m) => (
                      <tr key={m.id}>
                        <td>{m.order}</td>
                        <td>{m.title}</td>
                        <td>{m.content_type}</td>
                        <td>{m.duration_minutes}</td>
                        <td>
                          <Badge bg={m.is_published ? 'success' : 'secondary'}>
                            {m.is_published ? 'Published' : 'Draft'}
                          </Badge>
                        </td>
                        {(role === "admin" || role === "hr") && (
                          <td>
                            <div style={{ display: 'flex', gap: '5px' }}>
                              <Button size="sm" variant="info" onClick={() => viewModuleDetails(m.id)}>
                                View
                              </Button>
                              <Button size="sm" variant="warning" onClick={() => {
                                setEditModule({
                                  id: m.id,
                                  course: m.course,
                                  title: m.title,
                                  description: m.description || "",
                                  content_type: m.content_type,
                                  order: m.order,
                                  content: m.content || "",
                                  duration_minutes: m.duration_minutes,
                                  is_mandatory: m.is_mandatory,
                                  is_published: m.is_published,
                                });
                                setShowModuleEdit(true);
                              }}>
                                Edit
                              </Button>
                              <Button size="sm" variant="danger" onClick={() => deleteModule(m.id)}>
                                Delete
                              </Button>
                            </div>
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </>
          )}
        </Modal.Body>
      </Modal>

      {/* ========== CREATE MODULE MODAL ========== */}
      <Modal show={showModuleCreate} onHide={() => setShowModuleCreate(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Create Module</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <label className="form-label">Title *</label>
            <input
              className="form-control"
              value={newModule.title}
              onChange={(e) => setNewModule({ ...newModule, title: e.target.value })}
            />
          </div>
          
          <div className="mb-3">
            <label className="form-label">Description</label>
            <textarea
              className="form-control"
              rows="2"
              value={newModule.description}
              onChange={(e) => setNewModule({ ...newModule, description: e.target.value })}
            />
          </div>
          
          <div className="mb-3">
            <label className="form-label">Content Type *</label>
            <select
              className="form-control"
              value={newModule.content_type}
              onChange={(e) => setNewModule({ ...newModule, content_type: e.target.value })}
            >
              <option value="">Select Type</option>
              <option value="video">Video</option>
              <option value="reading">Reading</option>
              <option value="quiz">Quiz</option>
              <option value="assignment">Assignment</option>
              <option value="document">Document</option>
            </select>
          </div>
          
          <div className="mb-3">
            <label className="form-label">Order *</label>
            <input
              type="number"
              className="form-control"
              value={newModule.order}
              onChange={(e) => setNewModule({ ...newModule, order: e.target.value })}
            />
          </div>
          
          <div className="mb-3">
            <label className="form-label">Duration (minutes) *</label>
            <input
              type="number"
              className="form-control"
              value={newModule.duration_minutes}
              onChange={(e) => setNewModule({ ...newModule, duration_minutes: e.target.value })}
            />
          </div>
          
          <div className="mb-3">
            <label className="form-label">Content</label>
            <textarea
              className="form-control"
              rows="4"
              value={newModule.content}
              onChange={(e) => setNewModule({ ...newModule, content: e.target.value })}
            />
          </div>
          
          <div className="mb-3">
            <label>
              <input
                type="checkbox"
                checked={newModule.is_mandatory}
                onChange={(e) => setNewModule({ ...newModule, is_mandatory: e.target.checked })}
              /> Mandatory Module
            </label>
          </div>
          
          <div className="mb-3">
            <label>
              <input
                type="checkbox"
                checked={newModule.is_published}
                onChange={(e) => setNewModule({ ...newModule, is_published: e.target.checked })}
              /> Publish Immediately
            </label>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button onClick={createModule}>Create Module</Button>
        </Modal.Footer>
      </Modal>

      {/* ========== COURSE STATISTICS MODAL ========== */}
      <Modal show={showStats} onHide={() => setShowStats(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Course Statistics</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {courseStats && (
            <div>
              <p><strong>Total Enrollments:</strong> {courseStats.total_enrollments}</p>
              <p><strong>Active:</strong> {courseStats.active_enrollments}</p>
              <p><strong>Completed:</strong> {courseStats.completed_enrollments}</p>
              <p><strong>Pending Approval:</strong> {courseStats.pending_enrollments}</p>
              <p><strong>Average Progress:</strong> {courseStats.average_progress}%</p>
              <p><strong>Completion Rate:</strong> {courseStats.completion_rate}%</p>
              <p><strong>Total Modules:</strong> {courseStats.total_modules}</p>
            </div>
          )}
        </Modal.Body>
      </Modal>

      {/* ========== MY PROGRESS MODAL ========== */}
      <Modal show={showProgress} onHide={() => setShowProgress(false)} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>My Learning Progress</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {myProgress.length === 0 ? (
            <p className="text-muted">No progress data yet</p>
          ) : (
            <Table bordered size="sm">
              <thead>
                <tr>
                  <th>Module</th>
                  <th>Status</th>
                  <th>Time Spent (min)</th>
                  <th>Updated</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {myProgress.map((p) => (
                  <tr key={p.id}>
                    <td>{p.module_title}</td>
                    <td>
                      <Badge bg={p.status === 'completed' ? 'success' : p.status === 'in_progress' ? 'warning' : 'secondary'}>
                        {p.status}
                      </Badge>
                    </td>
                    <td>{p.time_spent_minutes}</td>
                    <td>{new Date(p.updated_at).toLocaleDateString()}</td>
                    <td>
                      {p.status === 'not_started' && (
                        <Button 
                          size="sm" 
                          variant="primary" 
                          onClick={() => updateProgress(p.module, 'in_progress', 0)}
                        >
                          Start
                        </Button>
                      )}
                      {p.status === 'in_progress' && (
                        <Button 
                          size="sm" 
                          variant="success" 
                          onClick={() => updateProgress(p.module, 'completed', p.time_spent_minutes + 30)}
                        >
                          Complete
                        </Button>
                      )}
                      {p.status === 'completed' && (
                        <Badge bg="success">✓ Done</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Modal.Body>
      </Modal>

      {/* ========== MODALS - DAY 21: QUIZZES ========== */}
      {/* Create Quiz Modal */}
      <Modal show={showQuizCreate} onHide={() => setShowQuizCreate(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Create Quiz</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <label className="form-label">Course ID *</label>
            <input type="number" className="form-control" placeholder="Course ID" value={newQuiz.course || ""} onChange={(e) => setNewQuiz({ ...newQuiz, course: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Module ID</label>
            <input type="number" className="form-control" placeholder="Module ID (optional)" value={newQuiz.module || ""} onChange={(e) => setNewQuiz({ ...newQuiz, module: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Title *</label>
            <input className="form-control" placeholder="Quiz Title" value={newQuiz.title} onChange={(e) => setNewQuiz({ ...newQuiz, title: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Description *</label>
            <textarea className="form-control" rows="3" value={newQuiz.description} onChange={(e) => setNewQuiz({ ...newQuiz, description: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Difficulty *</label>
            <select className="form-control" value={newQuiz.difficulty} onChange={(e) => setNewQuiz({ ...newQuiz, difficulty: e.target.value })}>
              <option value="">Select Difficulty</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          <div className="mb-3">
            <label className="form-label">Time Limit (minutes) *</label>
            <input type="number" className="form-control" value={newQuiz.time_limit_minutes} onChange={(e) => setNewQuiz({ ...newQuiz, time_limit_minutes: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Passing Score (%) *</label>
            <input type="number" className="form-control" value={newQuiz.passing_score} onChange={(e) => setNewQuiz({ ...newQuiz, passing_score: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Max Attempts *</label>
            <input type="number" className="form-control" value={newQuiz.max_attempts} onChange={(e) => setNewQuiz({ ...newQuiz, max_attempts: e.target.value })} />
          </div>
          <div className="mb-3">
            <label><input type="checkbox" checked={newQuiz.is_mandatory} onChange={(e) => setNewQuiz({ ...newQuiz, is_mandatory: e.target.checked })} /> Mandatory</label>
          </div>
          <div className="mb-3">
            <label><input type="checkbox" checked={newQuiz.randomize_questions} onChange={(e) => setNewQuiz({ ...newQuiz, randomize_questions: e.target.checked })} /> Randomize Questions</label>
          </div>
          <div className="mb-3">
            <label><input type="checkbox" checked={newQuiz.show_correct_answers} onChange={(e) => setNewQuiz({ ...newQuiz, show_correct_answers: e.target.checked })} /> Show Correct Answers</label>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowQuizCreate(false)}>Cancel</Button>
          <Button variant="primary" onClick={createQuiz}>Create Quiz</Button>
        </Modal.Footer>
      </Modal>

      {/* Edit Quiz Modal */}
      <Modal show={showQuizEdit} onHide={() => setShowQuizEdit(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Edit Quiz</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <label className="form-label">Course ID *</label>
            <input type="number" className="form-control" placeholder="Course ID" value={editQuiz.course || ""} onChange={(e) => setEditQuiz({ ...editQuiz, course: parseInt(e.target.value) || null })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Module ID</label>
            <input type="number" className="form-control" placeholder="Module ID (optional)" value={editQuiz.module || ""} onChange={(e) => setEditQuiz({ ...editQuiz, module: parseInt(e.target.value) || null })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Title *</label>
            <input className="form-control" placeholder="Quiz Title" value={editQuiz.title} onChange={(e) => setEditQuiz({ ...editQuiz, title: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Description *</label>
            <textarea className="form-control" rows="3" value={editQuiz.description} onChange={(e) => setEditQuiz({ ...editQuiz, description: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Difficulty *</label>
            <select className="form-control" value={editQuiz.difficulty} onChange={(e) => setEditQuiz({ ...editQuiz, difficulty: e.target.value })}>
              <option value="">Select Difficulty</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
          <div className="mb-3">
            <label className="form-label">Time Limit (minutes) *</label>
            <input type="number" className="form-control" value={editQuiz.time_limit_minutes} onChange={(e) => setEditQuiz({ ...editQuiz, time_limit_minutes: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Passing Score (%) *</label>
            <input type="number" className="form-control" value={editQuiz.passing_score} onChange={(e) => setEditQuiz({ ...editQuiz, passing_score: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Max Attempts *</label>
            <input type="number" className="form-control" value={editQuiz.max_attempts} onChange={(e) => setEditQuiz({ ...editQuiz, max_attempts: e.target.value })} />
          </div>
          <div className="mb-3">
            <label><input type="checkbox" checked={editQuiz.is_mandatory} onChange={(e) => setEditQuiz({ ...editQuiz, is_mandatory: e.target.checked })} /> Mandatory</label>
          </div>
          <div className="mb-3">
            <label><input type="checkbox" checked={editQuiz.randomize_questions} onChange={(e) => setEditQuiz({ ...editQuiz, randomize_questions: e.target.checked })} /> Randomize Questions</label>
          </div>
          <div className="mb-3">
            <label><input type="checkbox" checked={editQuiz.show_correct_answers} onChange={(e) => setEditQuiz({ ...editQuiz, show_correct_answers: e.target.checked })} /> Show Correct Answers</label>
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowQuizEdit(false)}>Cancel</Button>
          <Button variant="primary" onClick={updateQuiz}>Update Quiz</Button>
        </Modal.Footer>
      </Modal>

      {/* Take Quiz Modal */}
      <Modal show={showQuizTake} onHide={() => {
        setShowQuizTake(false);
        setQuizAnswers({}); // Clear answers when closing
      }} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>{selectedQuiz?.title}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedQuiz && (
            <>
              <p>{selectedQuiz.description}</p>
              <div className="mb-3">
                <Badge bg="info">Difficulty: {selectedQuiz.difficulty}</Badge>{' '}
                <Badge bg="warning">Time Limit: {selectedQuiz.time_limit_minutes} min</Badge>{' '}
                <Badge bg="success">Passing Score: {selectedQuiz.passing_score}%</Badge>
              </div>
              
              {selectedQuiz.questions && selectedQuiz.questions.length > 0 ? (
                <>
                  {selectedQuiz.questions.map((q, idx) => (
                    <div key={q.id} className="mb-4 p-3 border">
                      <h6>Q{idx + 1}. {q.question_text} ({q.points} points)</h6>
                      <div>
                        {q.question_type === 'single_choice' && q.options && q.options.map((opt, i) => (
                          <div key={i}>
                            <label>
                              <input 
                                type="radio" 
                                name={`q${q.id}`} 
                                value={opt}
                                checked={quizAnswers[q.id]?.answer?.[0] === opt}
                                onChange={() => setQuizAnswers({...quizAnswers, [q.id]: { answer: [opt] }})}
                              /> {opt}
                            </label>
                          </div>
                        ))}
                        
                        {q.question_type === 'multiple_choice' && q.options && q.options.map((opt, i) => (
                          <div key={i}>
                            <label>
                              <input 
                                type="checkbox" 
                                value={opt}
                                checked={(quizAnswers[q.id]?.answer || []).includes(opt)}
                                onChange={(e) => {
                                  const current = quizAnswers[q.id]?.answer || [];
                                  const updated = e.target.checked 
                                    ? [...current, opt] 
                                    : current.filter(a => a !== opt);
                                  setQuizAnswers({...quizAnswers, [q.id]: { answer: updated }});
                                }}
                              /> {opt}
                            </label>
                          </div>
                        ))}
                        
                        {q.question_type === 'true_false' && (
                          <>
                            <div>
                              <label>
                                <input 
                                  type="radio" 
                                  name={`q${q.id}`} 
                                  value="True"
                                  checked={quizAnswers[q.id]?.answer?.[0] === 'True'}
                                  onChange={() => setQuizAnswers({...quizAnswers, [q.id]: { answer: ['True'] }})}
                                /> True
                              </label>
                            </div>
                            <div>
                              <label>
                                <input 
                                  type="radio" 
                                  name={`q${q.id}`} 
                                  value="False"
                                  checked={quizAnswers[q.id]?.answer?.[0] === 'False'}
                                  onChange={() => setQuizAnswers({...quizAnswers, [q.id]: { answer: ['False'] }})}
                                /> False
                              </label>
                            </div>
                          </>
                        )}
                        
                        {q.question_type === 'text' && (
                          <textarea 
                            className="form-control" 
                            rows="3"
                            value={quizAnswers[q.id]?.answer?.[0] || ''}
                            onChange={(e) => setQuizAnswers({...quizAnswers, [q.id]: { answer: [e.target.value] }})}
                          />
                        )}
                      </div>
                    </div>
                  ))}
                </>
              ) : (
                <p className="text-muted">No questions available</p>
              )}
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => {
            setShowQuizTake(false);
            setQuizAnswers({});
          }}>Cancel</Button>
          <Button variant="success" onClick={() => submitQuiz(selectedQuiz?.id)}>Submit Quiz</Button>
        </Modal.Footer>
      </Modal>

      {/* Quiz Results Modal */}
      <Modal show={showQuizResults} onHide={() => setShowQuizResults(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Quiz Results</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {currentAttempt && (
            <>
              <h5 className="text-center">
                <Badge bg={currentAttempt.passed ? 'success' : 'danger'} style={{ fontSize: '1.2rem' }}>
                  Score: {currentAttempt.score} ({currentAttempt.percentage}%)
                </Badge>
              </h5>
              <p className="text-center">
                {currentAttempt.passed ? '🎉 Congratulations! You passed!' : '❌ You did not pass. Try again!'}
              </p>
              <div className="mt-3">
                <p><strong>Attempt #:</strong> {currentAttempt.attempt_number}</p>
                <p><strong>Time Taken:</strong> {currentAttempt.time_taken_minutes} minutes</p>
              </div>
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="primary" onClick={() => setShowQuizResults(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* ========== MODALS - DAY 21: CERTIFICATES ========== */}
      {/* Issue Certificate Modal */}
      <Modal show={showCertificateIssue} onHide={() => setShowCertificateIssue(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Issue Certificate</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <label className="form-label">User ID *</label>
            <input type="number" className="form-control" value={newCertificate.user || ""} onChange={(e) => setNewCertificate({ ...newCertificate, user: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Course ID *</label>
            <input type="number" className="form-control" value={newCertificate.course || ""} onChange={(e) => setNewCertificate({ ...newCertificate, course: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Enrollment ID</label>
            <input type="number" className="form-control" value={newCertificate.enrollment || ""} onChange={(e) => setNewCertificate({ ...newCertificate, enrollment: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Completion Score *</label>
            <input type="number" step="0.01" className="form-control" value={newCertificate.completion_score} onChange={(e) => setNewCertificate({ ...newCertificate, completion_score: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Quiz Average</label>
            <input type="number" step="0.01" className="form-control" value={newCertificate.quiz_average} onChange={(e) => setNewCertificate({ ...newCertificate, quiz_average: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Expiry Date *</label>
            <input type="date" className="form-control" value={newCertificate.expiry_date} onChange={(e) => setNewCertificate({ ...newCertificate, expiry_date: e.target.value })} />
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCertificateIssue(false)}>Cancel</Button>
          <Button variant="primary" onClick={issueCertificate}>Issue Certificate</Button>
        </Modal.Footer>
      </Modal>

      {/* Certificate Detail Modal */}
      <Modal show={showCertificateDetail} onHide={() => setShowCertificateDetail(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Certificate Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedCertificate && (
            <div>
              <h5>{selectedCertificate.title}</h5>
              <p><strong>Certificate ID:</strong> {selectedCertificate.certificate_id}</p>
              <p><strong>User:</strong> {selectedCertificate.user_name}</p>
              <p><strong>Course:</strong> {selectedCertificate.course_title}</p>
              <p><strong>Issued Date:</strong> {new Date(selectedCertificate.issued_date).toLocaleDateString()}</p>
              <p><strong>Expiry Date:</strong> {selectedCertificate.expiry_date ? new Date(selectedCertificate.expiry_date).toLocaleDateString() : 'N/A'}</p>
              <p><strong>Status:</strong> <Badge bg={selectedCertificate.status === 'active' ? 'success' : 'danger'}>{selectedCertificate.status}</Badge></p>
              <p><strong>Completion Score:</strong> {selectedCertificate.completion_score}%</p>
              {selectedCertificate.quiz_average && <p><strong>Quiz Average:</strong> {selectedCertificate.quiz_average}%</p>}
              {selectedCertificate.description && <p className="mt-3">{selectedCertificate.description}</p>}
            </div>
          )}
        </Modal.Body>
      </Modal>

      {/* ========== MODALS - DAY 21: SKILLS ========== */}
      {/* Create Skill Modal */}
      <Modal show={showSkillCreate} onHide={() => setShowSkillCreate(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Create Skill</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <label className="form-label">Name *</label>
            <input className="form-control" placeholder="Skill Name" value={newSkill.name} onChange={(e) => setNewSkill({ ...newSkill, name: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Category *</label>
            <select className="form-control" value={newSkill.category} onChange={(e) => setNewSkill({ ...newSkill, category: e.target.value })}>
              <option value="">Select Category</option>
              <option value="technical">Technical</option>
              <option value="soft_skill">Soft Skill</option>
              <option value="leadership">Leadership</option>
              <option value="compliance">Compliance</option>
              <option value="tool">Tool</option>
              <option value="certification">Certification</option>
            </select>
          </div>
          <div className="mb-3">
            <label className="form-label">Description *</label>
            <textarea className="form-control" rows="3" value={newSkill.description} onChange={(e) => setNewSkill({ ...newSkill, description: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Related Course IDs (comma-separated)</label>
            <input className="form-control" placeholder="e.g., 1,2,3" value={newSkill.related_courses.join(',')} onChange={(e) => setNewSkill({ ...newSkill, related_courses: e.target.value.split(',').filter(Boolean).map(Number) })} />
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowSkillCreate(false)}>Cancel</Button>
          <Button variant="primary" onClick={createSkill}>Create Skill</Button>
        </Modal.Footer>
      </Modal>

      {/* Edit Skill Modal */}
      <Modal show={showSkillEdit} onHide={() => setShowSkillEdit(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Skill</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <label className="form-label">Name *</label>
            <input className="form-control" placeholder="Skill Name" value={editSkill.name} onChange={(e) => setEditSkill({ ...editSkill, name: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Category *</label>
            <select className="form-control" value={editSkill.category} onChange={(e) => setEditSkill({ ...editSkill, category: e.target.value })}>
              <option value="">Select Category</option>
              <option value="technical">Technical</option>
              <option value="soft_skill">Soft Skill</option>
              <option value="leadership">Leadership</option>
              <option value="compliance">Compliance</option>
              <option value="tool">Tool</option>
              <option value="certification">Certification</option>
            </select>
          </div>
          <div className="mb-3">
            <label className="form-label">Description *</label>
            <textarea className="form-control" rows="3" value={editSkill.description} onChange={(e) => setEditSkill({ ...editSkill, description: e.target.value })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Related Course IDs (comma-separated)</label>
            <input className="form-control" placeholder="e.g., 1,2,3" value={editSkill.related_courses.join(',')} onChange={(e) => setEditSkill({ ...editSkill, related_courses: e.target.value.split(',').filter(Boolean).map(Number) })} />
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowSkillEdit(false)}>Cancel</Button>
          <Button variant="primary" onClick={updateSkill}>Update Skill</Button>
        </Modal.Footer>
      </Modal>

      {/* Skill Detail Modal */}
      <Modal show={showSkillDetail} onHide={() => setShowSkillDetail(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Skill Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedSkillDetail && (
            <>
              <h5>{selectedSkillDetail.name}</h5>
              <p><Badge>{selectedSkillDetail.category}</Badge></p>
              <p><strong>Description:</strong> {selectedSkillDetail.description || 'N/A'}</p>
              {selectedSkillDetail.related_courses_details && selectedSkillDetail.related_courses_details.length > 0 && (
                <>
                  <h6>Related Courses</h6>
                  <ul>
                    {selectedSkillDetail.related_courses_details.map((c) => (
                      <li key={c.id}>{c.title}</li>
                    ))}
                  </ul>
                </>
              )}
              <p className="text-muted"><small>Created: {new Date(selectedSkillDetail.created_at).toLocaleString()}</small></p>
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowSkillDetail(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* Users with Skill Modal */}
      <Modal show={showUsersWithSkill} onHide={() => setShowUsersWithSkill(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Users with this Skill</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {usersWithSkill.length === 0 ? (
            <p className="text-center text-muted">No users have this skill yet</p>
          ) : (
            <Table bordered hover>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Proficiency</th>
                  <th>Experience (years)</th>
                  <th>Endorsements</th>
                  <th>Last Updated</th>
                </tr>
              </thead>
              <tbody>
                {usersWithSkill.map((u, idx) => (
                  <tr key={idx}>
                    <td>{u.user_name}</td>
                    <td>
                      <Badge bg={
                        u.proficiency_level === 'expert' ? 'success' :
                        u.proficiency_level === 'advanced' ? 'info' :
                        u.proficiency_level === 'intermediate' ? 'primary' : 'secondary'
                      }>
                        {u.proficiency_level}
                      </Badge>
                    </td>
                    <td>{u.years_of_experience}</td>
                    <td>{u.endorsement_count || 0}</td>
                    <td>{new Date(u.last_updated).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowUsersWithSkill(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* Add User Skill Modal */}
      <Modal show={showUserSkillAdd} onHide={() => setShowUserSkillAdd(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Add My Skill</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <label className="form-label">Skill ID *</label>
            <input type="number" className="form-control" placeholder="Select from All Skills table" value={newUserSkill.skill || ""} onChange={(e) => setNewUserSkill({ ...newUserSkill, skill: parseInt(e.target.value) || null })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Proficiency Level *</label>
            <select className="form-control" value={newUserSkill.proficiency_level} onChange={(e) => setNewUserSkill({ ...newUserSkill, proficiency_level: e.target.value })}>
              <option value="">Select Level</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="expert">Expert</option>
            </select>
          </div>
          <div className="mb-3">
            <label className="form-label">Years of Experience *</label>
            <input type="number" step="0.1" className="form-control" value={newUserSkill.years_of_experience} onChange={(e) => setNewUserSkill({ ...newUserSkill, years_of_experience: parseFloat(e.target.value) || 0 })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Notes</label>
            <textarea className="form-control" rows="3" value={newUserSkill.notes} onChange={(e) => setNewUserSkill({ ...newUserSkill, notes: e.target.value })} />
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowUserSkillAdd(false)}>Cancel</Button>
          <Button variant="primary" onClick={addUserSkill}>Add Skill</Button>
        </Modal.Footer>
      </Modal>

      {/* Skill Gap Analysis Modal */}
      <Modal show={showSkillGap} onHide={() => setShowSkillGap(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Skill Gap Analysis</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {skillGapAnalysis && (
            <>
              <h6>Current Skills ({skillGapAnalysis.current_skills?.length || 0})</h6>
              {skillGapAnalysis.current_skills && skillGapAnalysis.current_skills.length > 0 ? (
                <ul>
                  {skillGapAnalysis.current_skills.map((s, idx) => (
                    <li key={idx}>{s.skill_name} - <Badge>{s.proficiency_level}</Badge></li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted">No current skills</p>
              )}

              <h6 className="mt-4">Recommended Skills ({skillGapAnalysis.recommended_skills?.length || 0})</h6>
              {skillGapAnalysis.recommended_skills && skillGapAnalysis.recommended_skills.length > 0 ? (
                <ul>
                  {skillGapAnalysis.recommended_skills.map((s, idx) => (
                    <li key={idx}>{s.skill_name} ({s.category})</li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted">No recommendations</p>
              )}

              <h6 className="mt-4">Skill Gaps ({skillGapAnalysis.skill_gaps?.length || 0})</h6>
              {skillGapAnalysis.skill_gaps && skillGapAnalysis.skill_gaps.length > 0 ? (
                <ul>
                  {skillGapAnalysis.skill_gaps.map((s, idx) => (
                    <li key={idx}>
                      <strong>{s.skill_name}</strong> ({s.category})
                      <br />
                      <small className="text-muted">{s.reason}</small>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-muted">No skill gaps identified</p>
              )}
            </>
          )}
        </Modal.Body>
      </Modal>

      {/* Edit User Skill Modal */}
      <Modal show={showUserSkillEdit} onHide={() => setShowUserSkillEdit(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Edit My Skill</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <label className="form-label">Skill ID *</label>
            <input type="number" className="form-control" disabled value={editUserSkill.skill || ""} />
          </div>
          <div className="mb-3">
            <label className="form-label">Proficiency Level *</label>
            <select className="form-control" value={editUserSkill.proficiency_level} onChange={(e) => setEditUserSkill({ ...editUserSkill, proficiency_level: e.target.value })}>
              <option value="">Select Level</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="expert">Expert</option>
            </select>
          </div>
          <div className="mb-3">
            <label className="form-label">Years of Experience *</label>
            <input type="number" step="0.1" className="form-control" value={editUserSkill.years_of_experience} onChange={(e) => setEditUserSkill({ ...editUserSkill, years_of_experience: parseFloat(e.target.value) || 0 })} />
          </div>
          <div className="mb-3">
            <label className="form-label">Notes</label>
            <textarea className="form-control" rows="3" value={editUserSkill.notes} onChange={(e) => setEditUserSkill({ ...editUserSkill, notes: e.target.value })} />
          </div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowUserSkillEdit(false)}>Cancel</Button>
          <Button variant="primary" onClick={updateUserSkill}>Update Skill</Button>
        </Modal.Footer>
      </Modal>

      {/* All User Skills Modal (Admin/HR) */}
      <Modal show={showAllUserSkills} onHide={() => setShowAllUserSkills(false)} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>All User Skills</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {allUserSkills.length === 0 ? (
            <p className="text-center text-muted">No user skills found</p>
          ) : (
            <Table bordered hover size="sm">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Skill</th>
                  <th>Category</th>
                  <th>Proficiency</th>
                  <th>Experience (years)</th>
                  <th>Endorsements</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {allUserSkills.map((us) => (
                  <tr key={us.id}>
                    <td>{us.user_name || `User ${us.user}`}</td>
                    <td>{us.skill_name}</td>
                    <td><Badge>{us.skill_category}</Badge></td>
                    <td>
                      <Badge bg={
                        us.proficiency_level === 'expert' ? 'success' :
                        us.proficiency_level === 'advanced' ? 'info' :
                        us.proficiency_level === 'intermediate' ? 'primary' : 'secondary'
                      }>
                        {us.proficiency_level}
                      </Badge>
                    </td>
                    <td>{us.years_of_experience}</td>
                    <td>{us.endorsement_count || 0}</td>
                    <td><small>{us.source || 'manual'}</small></td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAllUserSkills(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* Leaderboard Modal */}
      <Modal show={showLeaderboard} onHide={() => setShowLeaderboard(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Quiz Leaderboard</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {leaderboard.length === 0 ? (
            <p className="text-center text-muted">No attempts yet</p>
          ) : (
            <Table bordered hover>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>User</th>
                  <th>Score</th>
                  <th>Percentage</th>
                  <th>Attempt</th>
                  <th>Submitted</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.map((entry, idx) => (
                  <tr key={idx}>
                    <td>
                      <Badge bg={idx === 0 ? 'warning' : idx === 1 ? 'secondary' : idx === 2 ? 'info' : 'light'}>
                        #{entry.rank || (idx + 1)}
                      </Badge>
                    </td>
                    <td>{entry.user_name}</td>
                    <td>{entry.score}</td>
                    <td>{entry.percentage}%</td>
                    <td>Attempt {entry.attempt_number}</td>
                    <td>{new Date(entry.submitted_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowLeaderboard(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* Quiz Questions Management Modal */}
      <Modal show={showQuestionManage} onHide={() => setShowQuestionManage(false)} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>Manage Questions - {selectedQuizForQuestions?.title}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <Button variant="success" onClick={() => {
              setNewQuestion({
                quiz: selectedQuizForQuestions?.id,
                order: quizQuestions.length + 1,
                question_type: "single_choice",
                question_text: "",
                options: [],
                correct_answer: [],
                points: 1,
                explanation: ""
              });
              setShowQuestionCreate(true);
            }}>
              + Add Question
            </Button>
          </div>
          {quizQuestions.length === 0 ? (
            <p className="text-center text-muted">No questions added yet</p>
          ) : (
            <Table bordered hover size="sm">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Type</th>
                  <th>Question</th>
                  <th>Options</th>
                  <th>Points</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {quizQuestions.map((q, idx) => (
                  <tr key={q.id}>
                    <td>{q.order}</td>
                    <td><Badge>{q.question_type}</Badge></td>
                    <td>{q.question_text.substring(0, 50)}...</td>
                    <td>{q.options?.length || 0} options</td>
                    <td>{q.points}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        <Button size="sm" variant="warning" onClick={() => {
                          setEditQuestion(q);
                          setShowQuestionEdit(true);
                        }}>
                          Edit
                        </Button>
                        <Button size="sm" variant="danger" onClick={() => deleteQuestion(q.id, selectedQuizForQuestions?.id)}>
                          Delete
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowQuestionManage(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* Create Question Modal */}
      <Modal show={showQuestionCreate} onHide={() => setShowQuestionCreate(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Add Question</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Question Type *</Form.Label>
            <Form.Select value={newQuestion.question_type} onChange={e => setNewQuestion({ ...newQuestion, question_type: e.target.value })}>
              <option value="single_choice">Single Choice</option>
              <option value="multiple_choice">Multiple Choice</option>
              <option value="true_false">True/False</option>
              <option value="text">Text Answer</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Question Text *</Form.Label>
            <Form.Control 
              as="textarea" 
              rows={3} 
              value={newQuestion.question_text} 
              onChange={e => setNewQuestion({ ...newQuestion, question_text: e.target.value })} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Order</Form.Label>
            <Form.Control 
              type="number" 
              value={newQuestion.order} 
              onChange={e => setNewQuestion({ ...newQuestion, order: e.target.value })} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Points *</Form.Label>
            <Form.Control 
              type="number" 
              value={newQuestion.points} 
              onChange={e => setNewQuestion({ ...newQuestion, points: e.target.value })} 
            />
          </Form.Group>
          {(newQuestion.question_type === 'single_choice' || newQuestion.question_type === 'multiple_choice') && (
            <>
              <Form.Group className="mb-3">
                <Form.Label>Options (one per line) *</Form.Label>
                <Form.Control 
                  as="textarea" 
                  rows={5} 
                  placeholder="Enter options, one per line"
                  value={Array.isArray(newQuestion.options) ? newQuestion.options.join('\n') : ''}
                  onChange={e => setNewQuestion({ ...newQuestion, options: e.target.value.split('\n').filter(o => o.trim()) })} 
                />
                <Form.Text>Enter each option on a new line</Form.Text>
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Correct Answer(s) *</Form.Label>
                <Form.Control 
                  as="textarea" 
                  rows={2} 
                  placeholder={newQuestion.question_type === 'multiple_choice' ? "Enter correct options, one per line" : "Enter the correct option"}
                  value={Array.isArray(newQuestion.correct_answer) ? newQuestion.correct_answer.join('\n') : ''}
                  onChange={e => setNewQuestion({ ...newQuestion, correct_answer: e.target.value.split('\n').filter(a => a.trim()) })} 
                />
                <Form.Text>
                  {newQuestion.question_type === 'multiple_choice' 
                    ? 'Enter each correct option on a new line (for multiple correct answers)'
                    : 'Enter the exact text of the correct option'}
                </Form.Text>
              </Form.Group>
            </>
          )}
          {newQuestion.question_type === 'true_false' && (
            <Form.Group className="mb-3">
              <Form.Label>Correct Answer *</Form.Label>
              <Form.Select 
                value={Array.isArray(newQuestion.correct_answer) && newQuestion.correct_answer.length > 0 ? newQuestion.correct_answer[0] : ''}
                onChange={e => setNewQuestion({ ...newQuestion, correct_answer: [e.target.value] })}
              >
                <option value="">Select...</option>
                <option value="True">True</option>
                <option value="False">False</option>
              </Form.Select>
            </Form.Group>
          )}
          {newQuestion.question_type === 'text' && (
            <Form.Group className="mb-3">
              <Form.Label>Expected Answer (optional)</Form.Label>
              <Form.Control 
                type="text" 
                placeholder="Expected answer for reference"
                value={Array.isArray(newQuestion.correct_answer) && newQuestion.correct_answer.length > 0 ? newQuestion.correct_answer[0] : ''}
                onChange={e => setNewQuestion({ ...newQuestion, correct_answer: e.target.value ? [e.target.value] : [] })} 
              />
              <Form.Text>Optional - for instructor reference</Form.Text>
            </Form.Group>
          )}
          <Form.Group className="mb-3">
            <Form.Label>Explanation (optional)</Form.Label>
            <Form.Control 
              as="textarea" 
              rows={2} 
              placeholder="Explanation shown after answering"
              value={newQuestion.explanation} 
              onChange={e => setNewQuestion({ ...newQuestion, explanation: e.target.value })} 
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowQuestionCreate(false)}>Cancel</Button>
          <Button variant="primary" onClick={createQuestion}>Create Question</Button>
        </Modal.Footer>
      </Modal>

      {/* Edit Question Modal */}
      <Modal show={showQuestionEdit} onHide={() => setShowQuestionEdit(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Edit Question</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Question Type *</Form.Label>
            <Form.Select value={editQuestion.question_type} onChange={e => setEditQuestion({ ...editQuestion, question_type: e.target.value })}>
              <option value="single_choice">Single Choice</option>
              <option value="multiple_choice">Multiple Choice</option>
              <option value="true_false">True/False</option>
              <option value="text">Text Answer</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Question Text *</Form.Label>
            <Form.Control 
              as="textarea" 
              rows={3} 
              value={editQuestion.question_text} 
              onChange={e => setEditQuestion({ ...editQuestion, question_text: e.target.value })} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Order</Form.Label>
            <Form.Control 
              type="number" 
              value={editQuestion.order} 
              onChange={e => setEditQuestion({ ...editQuestion, order: e.target.value })} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Points *</Form.Label>
            <Form.Control 
              type="number" 
              value={editQuestion.points} 
              onChange={e => setEditQuestion({ ...editQuestion, points: e.target.value })} 
            />
          </Form.Group>
          {(editQuestion.question_type === 'single_choice' || editQuestion.question_type === 'multiple_choice') && (
            <>
              <Form.Group className="mb-3">
                <Form.Label>Options (one per line) *</Form.Label>
                <Form.Control 
                  as="textarea" 
                  rows={5} 
                  placeholder="Enter options, one per line"
                  value={Array.isArray(editQuestion.options) ? editQuestion.options.join('\n') : ''}
                  onChange={e => setEditQuestion({ ...editQuestion, options: e.target.value.split('\n').filter(o => o.trim()) })} 
                />
                <Form.Text>Enter each option on a new line</Form.Text>
              </Form.Group>
              <Form.Group className="mb-3">
                <Form.Label>Correct Answer(s) *</Form.Label>
                <Form.Control 
                  as="textarea" 
                  rows={2} 
                  placeholder={editQuestion.question_type === 'multiple_choice' ? "Enter correct options, one per line" : "Enter the correct option"}
                  value={Array.isArray(editQuestion.correct_answer) ? editQuestion.correct_answer.join('\n') : ''}
                  onChange={e => setEditQuestion({ ...editQuestion, correct_answer: e.target.value.split('\n').filter(a => a.trim()) })} 
                />
                <Form.Text>
                  {editQuestion.question_type === 'multiple_choice' 
                    ? 'Enter each correct option on a new line (for multiple correct answers)'
                    : 'Enter the exact text of the correct option'}
                </Form.Text>
              </Form.Group>
            </>
          )}
          {editQuestion.question_type === 'true_false' && (
            <Form.Group className="mb-3">
              <Form.Label>Correct Answer *</Form.Label>
              <Form.Select 
                value={Array.isArray(editQuestion.correct_answer) && editQuestion.correct_answer.length > 0 ? editQuestion.correct_answer[0] : ''}
                onChange={e => setEditQuestion({ ...editQuestion, correct_answer: [e.target.value] })}
              >
                <option value="">Select...</option>
                <option value="True">True</option>
                <option value="False">False</option>
              </Form.Select>
            </Form.Group>
          )}
          {editQuestion.question_type === 'text' && (
            <Form.Group className="mb-3">
              <Form.Label>Expected Answer (optional)</Form.Label>
              <Form.Control 
                type="text" 
                placeholder="Expected answer for reference"
                value={Array.isArray(editQuestion.correct_answer) && editQuestion.correct_answer.length > 0 ? editQuestion.correct_answer[0] : ''}
                onChange={e => setEditQuestion({ ...editQuestion, correct_answer: e.target.value ? [e.target.value] : [] })} 
              />
              <Form.Text>Optional - for instructor reference</Form.Text>
            </Form.Group>
          )}
          <Form.Group className="mb-3">
            <Form.Label>Explanation (optional)</Form.Label>
            <Form.Control 
              as="textarea" 
              rows={2} 
              placeholder="Explanation shown after answering"
              value={editQuestion.explanation} 
              onChange={e => setEditQuestion({ ...editQuestion, explanation: e.target.value })} 
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowQuestionEdit(false)}>Cancel</Button>
          <Button variant="primary" onClick={updateQuestion}>Update Question</Button>
        </Modal.Footer>
      </Modal>

      {/* Edit Course Modal */}
      <Modal show={showCourseEdit} onHide={() => setShowCourseEdit(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Edit Course</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Title *</Form.Label>
            <Form.Control 
              value={editCourse.title} 
              onChange={e => setEditCourse({...editCourse, title: e.target.value})} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control 
              as="textarea" 
              rows={3} 
              value={editCourse.description} 
              onChange={e => setEditCourse({...editCourse, description: e.target.value})} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Category *</Form.Label>
            <Form.Select value={editCourse.category} onChange={e => setEditCourse({...editCourse, category: e.target.value})}>
              <option value="">Select...</option>
              <option value="technical">Technical</option>
              <option value="leadership">Leadership</option>
              <option value="compliance">Compliance</option>
              <option value="soft_skills">Soft Skills</option>
              <option value="onboarding">Onboarding</option>
              <option value="professional">Professional</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Level *</Form.Label>
            <Form.Select value={editCourse.level} onChange={e => setEditCourse({...editCourse, level: e.target.value})}>
              <option value="">Select...</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Duration (hours) *</Form.Label>
            <Form.Control 
              type="number" 
              value={editCourse.duration_hours} 
              onChange={e => setEditCourse({...editCourse, duration_hours: e.target.value})} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Learning Objectives</Form.Label>
            <Form.Control 
              as="textarea" 
              rows={2} 
              value={editCourse.learning_objectives} 
              onChange={e => setEditCourse({...editCourse, learning_objectives: e.target.value})} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Check 
              type="checkbox" 
              label="Mandatory" 
              checked={editCourse.is_mandatory} 
              onChange={e => setEditCourse({...editCourse, is_mandatory: e.target.checked})} 
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCourseEdit(false)}>Cancel</Button>
          <Button variant="primary" onClick={updateCourse}>Update Course</Button>
        </Modal.Footer>
      </Modal>

      {/* Edit Module Modal */}
      <Modal show={showModuleEdit} onHide={() => setShowModuleEdit(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Module</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Title *</Form.Label>
            <Form.Control 
              value={editModule.title} 
              onChange={e => setEditModule({...editModule, title: e.target.value})} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Description</Form.Label>
            <Form.Control 
              as="textarea" 
              rows={2} 
              value={editModule.description} 
              onChange={e => setEditModule({...editModule, description: e.target.value})} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Content Type *</Form.Label>
            <Form.Select value={editModule.content_type} onChange={e => setEditModule({...editModule, content_type: e.target.value})}>
              <option value="">Select...</option>
              <option value="video">Video</option>
              <option value="reading">Reading</option>
              <option value="quiz">Quiz</option>
              <option value="document">Document</option>
              <option value="assignment">Assignment</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Order *</Form.Label>
            <Form.Control 
              type="number" 
              value={editModule.order} 
              onChange={e => setEditModule({...editModule, order: e.target.value})} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Duration (minutes) *</Form.Label>
            <Form.Control 
              type="number" 
              value={editModule.duration_minutes} 
              onChange={e => setEditModule({...editModule, duration_minutes: e.target.value})} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Content</Form.Label>
            <Form.Control 
              as="textarea" 
              rows={3} 
              value={editModule.content} 
              onChange={e => setEditModule({...editModule, content: e.target.value})} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Check 
              type="checkbox" 
              label="Mandatory" 
              checked={editModule.is_mandatory} 
              onChange={e => setEditModule({...editModule, is_mandatory: e.target.checked})} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Check 
              type="checkbox" 
              label="Published" 
              checked={editModule.is_published} 
              onChange={e => setEditModule({...editModule, is_published: e.target.checked})} 
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModuleEdit(false)}>Cancel</Button>
          <Button variant="primary" onClick={updateModule}>Update Module</Button>
        </Modal.Footer>
      </Modal>

      {/* Module Detail Modal */}
      <Modal show={showModuleDetail} onHide={() => setShowModuleDetail(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Module Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedModuleDetail && (
            <>
              <p><strong>Title:</strong> {selectedModuleDetail.title}</p>
              <p><strong>Description:</strong> {selectedModuleDetail.description || 'N/A'}</p>
              <p><strong>Content Type:</strong> <Badge>{selectedModuleDetail.content_type}</Badge></p>
              <p><strong>Order:</strong> {selectedModuleDetail.order}</p>
              <p><strong>Duration:</strong> {selectedModuleDetail.duration_minutes} minutes</p>
              <p><strong>Mandatory:</strong> {selectedModuleDetail.is_mandatory ? 'Yes' : 'No'}</p>
              <p><strong>Status:</strong> <Badge bg={selectedModuleDetail.is_published ? 'success' : 'secondary'}>
                {selectedModuleDetail.is_published ? 'Published' : 'Draft'}
              </Badge></p>
              <hr />
              <p><strong>Content:</strong></p>
              <div style={{ whiteSpace: 'pre-wrap', background: '#f8f9fa', padding: '10px', borderRadius: '5px' }}>
                {selectedModuleDetail.content || 'No content added yet'}
              </div>
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowModuleDetail(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* All Modules Modal */}
      <Modal show={showAllModules} onHide={() => setShowAllModules(false)} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>All Modules</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {allModules.length === 0 ? (
            <p className="text-center text-muted">No modules found</p>
          ) : (
            <Table bordered hover size="sm">
              <thead>
                <tr>
                  <th>Course</th>
                  <th>Order</th>
                  <th>Title</th>
                  <th>Type</th>
                  <th>Duration</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {allModules.map((m) => (
                  <tr key={m.id}>
                    <td>{m.course_title || `Course ${m.course}`}</td>
                    <td>{m.order}</td>
                    <td>{m.title}</td>
                    <td><Badge>{m.content_type}</Badge></td>
                    <td>{m.duration_minutes} min</td>
                    <td>
                      <Badge bg={m.is_published ? 'success' : 'secondary'}>
                        {m.is_published ? 'Published' : 'Draft'}
                      </Badge>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        <Button size="sm" variant="info" onClick={() => viewModuleDetails(m.id)}>View</Button>
                        <Button size="sm" variant="warning" onClick={() => {
                          setEditModule({
                            id: m.id,
                            course: m.course,
                            title: m.title,
                            description: m.description || "",
                            content_type: m.content_type,
                            order: m.order,
                            content: m.content || "",
                            duration_minutes: m.duration_minutes,
                            is_mandatory: m.is_mandatory,
                            is_published: m.is_published,
                          });
                          setShowModuleEdit(true);
                        }}>Edit</Button>
                        <Button size="sm" variant="danger" onClick={() => deleteModule(m.id)}>Delete</Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAllModules(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* All Enrollments Modal */}
      <Modal show={showAllEnrollments} onHide={() => setShowAllEnrollments(false)} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>All Enrollments</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            {(role === 'admin' || role === 'hr') && (
              <Button variant="success" size="sm" onClick={() => setShowEnrollmentCreate(true)}>
                + Create Enrollment
              </Button>
            )}
          </div>
          {allEnrollments.length === 0 ? (
            <p className="text-center text-muted">No enrollments found</p>
          ) : (
            <Table bordered hover size="sm">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Course</th>
                  <th>Status</th>
                  <th>Progress</th>
                  <th>Deadline</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {allEnrollments.map((e) => (
                  <tr key={e.id}>
                    <td>{e.user_name || `User ${e.user}`}</td>
                    <td>{e.course_title || `Course ${e.course}`}</td>
                    <td>
                      <Badge bg={
                        e.status === 'completed' ? 'success' :
                        e.status === 'active' ? 'primary' :
                        e.status === 'pending' ? 'warning' : 'secondary'
                      }>
                        {e.status}
                      </Badge>
                    </td>
                    <td>
                      <ProgressBar now={parseFloat(e.progress_percentage || 0)} label={`${e.progress_percentage || 0}%`} />
                    </td>
                    <td>{e.deadline ? new Date(e.deadline).toLocaleDateString() : 'N/A'}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        <Button size="sm" variant="info" onClick={() => viewEnrollmentDetails(e.id)}>View</Button>
                        {(role === 'admin' || role === 'hr') && (
                          <>
                            <Button size="sm" variant="warning" onClick={() => {
                              setEditEnrollment({
                                id: e.id,
                                user: e.user,
                                course: e.course,
                                status: e.status,
                                deadline: e.deadline || "",
                                final_score: e.final_score || "",
                              });
                              setShowEnrollmentEdit(true);
                            }}>Edit</Button>
                            {e.status === 'pending' && (
                              <Button size="sm" variant="success" onClick={() => approveEnrollment(e.id)}>Approve</Button>
                            )}
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAllEnrollments(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* Create Enrollment Modal */}
      <Modal show={showEnrollmentCreate} onHide={() => setShowEnrollmentCreate(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Create Enrollment</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>User ID *</Form.Label>
            <Form.Control 
              type="number"
              value={newEnrollment.user || ''} 
              onChange={e => setNewEnrollment({...newEnrollment, user: e.target.value})} 
              placeholder="Enter user ID"
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Course ID *</Form.Label>
            <Form.Control 
              type="number"
              value={newEnrollment.course || ''} 
              onChange={e => setNewEnrollment({...newEnrollment, course: e.target.value})} 
              placeholder="Enter course ID"
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Deadline</Form.Label>
            <Form.Control 
              type="date"
              value={newEnrollment.deadline} 
              onChange={e => setNewEnrollment({...newEnrollment, deadline: e.target.value})} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Status</Form.Label>
            <Form.Select value={newEnrollment.status} onChange={e => setNewEnrollment({...newEnrollment, status: e.target.value})}>
              <option value="active">Active</option>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
              <option value="dropped">Dropped</option>
            </Form.Select>
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEnrollmentCreate(false)}>Cancel</Button>
          <Button variant="primary" onClick={createEnrollment}>Create Enrollment</Button>
        </Modal.Footer>
      </Modal>

      {/* Edit Enrollment Modal */}
      <Modal show={showEnrollmentEdit} onHide={() => setShowEnrollmentEdit(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Edit Enrollment</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Group className="mb-3">
            <Form.Label>Status *</Form.Label>
            <Form.Select value={editEnrollment.status} onChange={e => setEditEnrollment({...editEnrollment, status: e.target.value})}>
              <option value="active">Active</option>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
              <option value="dropped">Dropped</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Deadline</Form.Label>
            <Form.Control 
              type="date"
              value={editEnrollment.deadline} 
              onChange={e => setEditEnrollment({...editEnrollment, deadline: e.target.value})} 
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>Final Score</Form.Label>
            <Form.Control 
              type="number"
              value={editEnrollment.final_score} 
              onChange={e => setEditEnrollment({...editEnrollment, final_score: e.target.value})} 
            />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEnrollmentEdit(false)}>Cancel</Button>
          <Button variant="primary" onClick={updateEnrollment}>Update Enrollment</Button>
        </Modal.Footer>
      </Modal>

      {/* Enrollment Detail Modal */}
      <Modal show={showEnrollmentDetail} onHide={() => setShowEnrollmentDetail(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Enrollment Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedEnrollmentDetail && (
            <>
              <p><strong>User:</strong> {selectedEnrollmentDetail.user_name || `User ${selectedEnrollmentDetail.user}`}</p>
              <p><strong>Course:</strong> {selectedEnrollmentDetail.course_title || `Course ${selectedEnrollmentDetail.course}`}</p>
              <p><strong>Status:</strong> <Badge bg={
                selectedEnrollmentDetail.status === 'completed' ? 'success' :
                selectedEnrollmentDetail.status === 'active' ? 'primary' :
                selectedEnrollmentDetail.status === 'pending' ? 'warning' : 'secondary'
              }>
                {selectedEnrollmentDetail.status}
              </Badge></p>
              <p><strong>Progress:</strong> {selectedEnrollmentDetail.progress_percentage || 0}%</p>
              <p><strong>Modules Completed:</strong> {selectedEnrollmentDetail.modules_completed || 0}</p>
              <p><strong>Enrolled:</strong> {selectedEnrollmentDetail.enrolled_at ? new Date(selectedEnrollmentDetail.enrolled_at).toLocaleString() : 'N/A'}</p>
              <p><strong>Deadline:</strong> {selectedEnrollmentDetail.deadline ? new Date(selectedEnrollmentDetail.deadline).toLocaleDateString() : 'N/A'}</p>
              {selectedEnrollmentDetail.completed_at && (
                <p><strong>Completed:</strong> {new Date(selectedEnrollmentDetail.completed_at).toLocaleString()}</p>
              )}
              {selectedEnrollmentDetail.final_score && (
                <p><strong>Final Score:</strong> {selectedEnrollmentDetail.final_score}</p>
              )}
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEnrollmentDetail(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* All Progress Modal */}
      <Modal show={showAllProgress} onHide={() => setShowAllProgress(false)} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>All Module Progress</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {allProgress.length === 0 ? (
            <p className="text-center text-muted">No progress records found</p>
          ) : (
            <Table bordered hover size="sm">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Course</th>
                  <th>Module</th>
                  <th>Status</th>
                  <th>Time Spent</th>
                  <th>Started</th>
                  <th>Completed</th>
                </tr>
              </thead>
              <tbody>
                {allProgress.map((p) => (
                  <tr key={p.id}>
                    <td>{p.user_name || 'N/A'}</td>
                    <td>{p.course_title || 'N/A'}</td>
                    <td>{p.module_title || `Module ${p.module}`}</td>
                    <td>
                      <Badge bg={
                        p.status === 'completed' ? 'success' :
                        p.status === 'in_progress' ? 'primary' : 'secondary'
                      }>
                        {p.status}
                      </Badge>
                    </td>
                    <td>{p.time_spent_minutes || 0} min</td>
                    <td>{p.started_at ? new Date(p.started_at).toLocaleString() : 'N/A'}</td>
                    <td>{p.completed_at ? new Date(p.completed_at).toLocaleString() : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAllProgress(false)}>Close</Button>
        </Modal.Footer>
      </Modal>


      {loading && <p>Loading...</p>}
    </div>
  );
}
