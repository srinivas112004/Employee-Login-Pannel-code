const LMS_API = "http://localhost:8000/api/lms";
const AUTH_API = "http://localhost:8000/api/auth";

const getToken = () => localStorage.getItem("access_token");

const request = async (url, options = {}) => {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
    },
  });

  let data = {};
  try { data = await res.json(); } catch {}

  if (!res.ok) throw data;
  return data;
};

const LMS = {
  // Courses
  getCourses: (filters = {}) => {
    const params = new URLSearchParams(filters).toString();
    return request(`${LMS_API}/courses/${params ? "?" + params : ""}`);
  },
  createCourse: (data) => request(`${LMS_API}/courses/`, { method: "POST", body: JSON.stringify(data) }),
  updateCourse: (id, data) => request(`${LMS_API}/courses/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteCourse: (id) => request(`${LMS_API}/courses/${id}/`, { method: "DELETE" }),
  publishCourse: (id) => request(`${LMS_API}/courses/${id}/publish/`, { method: "POST" }),
  archiveCourse: (id) => request(`${LMS_API}/courses/${id}/archive/`, { method: "POST" }),
  getCourseStats: (id) => request(`${LMS_API}/courses/${id}/statistics/`),

  // Modules
  getModules: (courseId = null) => request(`${LMS_API}/modules/${courseId ? "?course=" + courseId : ""}`),
  createModule: (data) => request(`${LMS_API}/modules/`, { method: "POST", body: JSON.stringify(data) }),
  updateModule: (id, data) => request(`${LMS_API}/modules/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteModule: (id) => request(`${LMS_API}/modules/${id}/`, { method: "DELETE" }),

  // Profile
  getProfile: () => request(`${AUTH_API}/profile/`),

  // Enrollments
  enrollCourse: (courseId) => request(`${LMS_API}/enrollments/enroll/`, { method: "POST", body: JSON.stringify({ course: courseId }) }),
  getMyCourses: () => request(`${LMS_API}/enrollments/my_courses/`),
  getPendingEnrollments: () => request(`${LMS_API}/enrollments/pending/`),
  approveEnrollment: (id) => request(`${LMS_API}/enrollments/${id}/approve/`, { method: "POST" }),
  rejectEnrollment: (id) => request(`${LMS_API}/enrollments/${id}/drop/`, { method: "POST" }),

  // Progress
  getAllProgress: () => request(`${LMS_API}/progress/`),
  getMyProgress: () => request(`${LMS_API}/progress/my_progress/`),
  updateProgress: (data) => request(`${LMS_API}/progress/update_progress/`, { method: "POST", body: JSON.stringify(data) }),
};

export default LMS;
