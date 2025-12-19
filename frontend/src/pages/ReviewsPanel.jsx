// src/pages/ReviewsPanel.jsx
import React, { useEffect, useState, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import ReviewsAPI from "../api/reviews";

/*
  ReviewsPanel.jsx - Day 19 frontend panel (complete, manager-review deadline fix)
  - Shows cycles, pending, my reviews, self-assessments, manager reviews
  - Cycle details & stats open in Bootstrap-style modals (not alerts)
  - Manager review submit checks deadline inclusively (end of day)
  - Pre-checks deadlines and permissions client-side
*/

function simpleDate(d) {
  if (!d) return "-";
  try {
    const dt = new Date(d);
    if (isNaN(dt)) return d;
    return dt.toLocaleDateString();
  } catch {
    return d;
  }
}

function formatServerError(err) {
  if (!err) return "Unknown error";
  if (err.body) {
    if (typeof err.body === "string") return err.body;
    try {
      const parts = [];
      for (const k of Object.keys(err.body)) {
        const v = err.body[k];
        if (Array.isArray(v)) parts.push(`${k}: ${v.join(", ")}`);
        else if (typeof v === "object") parts.push(`${k}: ${JSON.stringify(v)}`);
        else parts.push(`${k}: ${String(v)}`);
      }
      return parts.join("\n");
    } catch {
      return JSON.stringify(err.body);
    }
  }
  return err.message || String(err);
}

export default function ReviewsPanel() {
  const { user } = useAuth() || {};
  const role = ((user && user.role) || "employee").toLowerCase();
  const isAdmin = role === "admin";
  const isHR = role === "hr";
  const isManager = role === "manager";
  const isEmployee = role === "employee";
  const isIntern = role === "intern";

  const mountedRef = useRef(true);
  const [loading, setLoading] = useState(false);

  // Lists
  const [cycles, setCycles] = useState([]);
  const [myReviews, setMyReviews] = useState([]);
  const [pending, setPending] = useState([]);
  const [allReviews, setAllReviews] = useState([]);
  const [managerReviews, setManagerReviews] = useState([]);
  const [selfAssessments, setSelfAssessments] = useState([]);

  // Cycle form
  const [showCycleForm, setShowCycleForm] = useState(false);
  const [cycleForm, setCycleForm] = useState({
    id: null,
    name: "",
    review_type: "quarterly",
    description: "",
    start_date: "",
    end_date: "",
    self_review_deadline: "",
    manager_review_deadline: "",
    peer_review_deadline: "",
    status: "draft",
    participants: [],
  });

  // Create review
  const [showCreateReview, setShowCreateReview] = useState(false);
  const [createReviewForm, setCreateReviewForm] = useState({ cycle: "", employee: "", reviewer: "" });

  // Self assessment modal + mode
  const [showSelfForm, setShowSelfForm] = useState(false);
  const [selfMode, setSelfMode] = useState("create"); // create | view | edit
  const [selfForm, setSelfForm] = useState({
    id: null,
    review: "",
    accomplishments: "",
    challenges_faced: "",
    skills_developed: "",
    quality_of_work: 3,
    productivity: 3,
    communication: 3,
    teamwork: 3,
    initiative: 3,
    goals_achieved: "",
    goals_for_next_period: "",
    overall_rating: null,
    additional_comments: "",
  });
  const [selfNotice, setSelfNotice] = useState("");

  // Peer feedback
  const [showPeerForm, setShowPeerForm] = useState(false);
  const [peerForm, setPeerForm] = useState({
    review: "",
    collaboration_feedback: "",
    strengths: "",
    areas_for_improvement: "",
    teamwork: 3,
    communication: 3,
    reliability: 3,
    helpfulness: 3,
    overall_rating: 3,
    additional_comments: "",
    is_anonymous: false,
  });

  // Manager review modal
  const [showManagerForm, setShowManagerForm] = useState(false);
  const [managerMode, setManagerMode] = useState("create"); // create|view|edit
  const [managerForm, setManagerForm] = useState({
    id: null,
    review: "",
    performance_summary: "",
    strengths: "",
    areas_for_improvement: "",
    quality_of_work: 3,
    productivity: 3,
    communication: 3,
    teamwork: 3,
    initiative: 3,
    leadership: 3,
    problem_solving: 3,
    goals_achievement_comment: "",
    goals_for_next_period: "",
    promotion_recommendation: false,
    salary_increase_recommendation: false,
    training_recommendations: "",
    overall_rating: null,
    manager_comments: "",
  });

  // Stats modal
  const [showStatsModal, setShowStatsModal] = useState(false);
  const [statsData, setStatsData] = useState(null);

  // Cycle details modal
  const [showCycleDetails, setShowCycleDetails] = useState(false);
  const [cycleDetails, setCycleDetails] = useState(null);

  useEffect(() => {
    mountedRef.current = true;
    loadAll();
    return () => (mountedRef.current = false);
    // eslint-disable-next-line
  }, []);

  async function loadAll() {
    setLoading(true);
    try {
      const [
        cyclesResp,
        myResp,
        pendingResp,
        allResp,
        managerResp,
        selfListResp,
      ] = await Promise.allSettled([
        ReviewsAPI.listReviewCycles(),
        ReviewsAPI.myReviews(),
        ReviewsAPI.pendingReviews(),
        ReviewsAPI.listReviews(), // Load for all users so employees can select reviews for peer feedback
        (isManager || isAdmin || isHR) ? ReviewsAPI.listManagerReviews() : Promise.resolve({}),
        ReviewsAPI.listSelfAssessments(),
      ]);

      if (cyclesResp.status === "fulfilled")
        setCycles(Array.isArray(cyclesResp.value) ? cyclesResp.value : cyclesResp.value?.results || []);
      if (myResp.status === "fulfilled")
        setMyReviews(Array.isArray(myResp.value) ? myResp.value : myResp.value?.results || []);
      if (pendingResp.status === "fulfilled")
        setPending(Array.isArray(pendingResp.value) ? pendingResp.value : pendingResp.value?.results || []);
      if (allResp.status === "fulfilled") {
        const reviews = Array.isArray(allResp.value) ? allResp.value : allResp.value?.results || [];
        console.log('[ReviewsPanel] All reviews loaded:', reviews);
        console.log('[ReviewsPanel] Current user ID:', user?.id);
        console.log('[ReviewsPanel] Filtered reviews (excluding own):', reviews.filter(r => Number(r.employee) !== Number(user?.id)));
        setAllReviews(reviews);
      } else {
        console.error('[ReviewsPanel] Failed to load all reviews:', allResp.reason);
      }
      if (managerResp.status === "fulfilled" && (isManager || isAdmin || isHR))
        setManagerReviews(Array.isArray(managerResp.value) ? managerResp.value : managerResp.value?.results || []);
      if (selfListResp.status === "fulfilled")
        setSelfAssessments(Array.isArray(selfListResp.value) ? selfListResp.value : selfListResp.value?.results || []);

      [cyclesResp, myResp, pendingResp, allResp, managerResp, selfListResp].forEach((r, idx) => {
        if (r && r.status === "rejected") console.warn("loadAll rejected idx", idx, r.reason);
      });
    } catch (err) {
      console.error("loadAll error", err);
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }

  /* ---------------- helpers ---------------- */

  async function resolveCycle(cycleId) {
    if (!cycleId) return null;
    const found = cycles.find(c => Number(c.id) === Number(cycleId));
    if (found) return found;
    try {
      return await ReviewsAPI.getReviewCycle(cycleId);
    } catch (e) {
      return null;
    }
  }

  function deadlinePassedForCycleObj(cycle) {
    if (!cycle || !cycle.self_review_deadline) return false;
    const dl = new Date(cycle.self_review_deadline);
    if (isNaN(dl)) return false;
    const now = new Date();
    // treat deadline as end of day inclusive
    const dlEnd = new Date(dl.getTime());
    dlEnd.setHours(23, 59, 59, 999);
    return now > dlEnd;
  }

  function deadlinePassedForReviewCached(review) {
    if (!review) return false;
    const c = cycles.find(cy => Number(cy.id) === Number(review.cycle));
    if (c) return deadlinePassedForCycleObj(c);
    return false;
  }

  function openCycleDetails(cycle) {
    setCycleDetails(cycle);
    setShowCycleDetails(true);
  }

  function closeCycleDetails() {
    setCycleDetails(null);
    setShowCycleDetails(false);
  }

  /* ---------------- cycle form actions ---------------- */

  function validateCycle() {
    const required = ["name", "start_date", "end_date", "self_review_deadline", "manager_review_deadline", "participants"];
    const missing = required.filter((k) => {
      const v = cycleForm[k];
      if (Array.isArray(v)) return v.length === 0;
      return !v || String(v).trim() === "";
    });
    if (missing.length) return `Missing: ${missing.join(", ")}`;

    const start = new Date(cycleForm.start_date);
    const end = new Date(cycleForm.end_date);
    const selfD = new Date(cycleForm.self_review_deadline);
    const manD = new Date(cycleForm.manager_review_deadline);
    if (isNaN(start) || isNaN(end) || isNaN(selfD) || isNaN(manD)) return "Dates must be valid (YYYY-MM-DD).";
    if (start > end) return "Start must be <= end.";
    if (selfD <= end) return "Self-review deadline should be after review period end date.";
    if (manD <= selfD) return "Manager review deadline should be after self-review deadline";
    return null;
  }

  async function submitCycle(e) {
    e && e.preventDefault && e.preventDefault();
    if (!(isAdmin || isHR)) { alert("Only Admin/HR can create or edit review cycles"); return; }
    const v = validateCycle();
    if (v) { alert(v); return; }
    setLoading(true);
    try {
      const payload = {
        name: cycleForm.name,
        review_type: cycleForm.review_type,
        description: cycleForm.description,
        start_date: cycleForm.start_date,
        end_date: cycleForm.end_date,
        self_review_deadline: cycleForm.self_review_deadline,
        manager_review_deadline: cycleForm.manager_review_deadline,
        peer_review_deadline: cycleForm.peer_review_deadline || undefined,
        status: cycleForm.status,
        participants: cycleForm.participants,
      };
      if (cycleForm.id) {
        await ReviewsAPI.patchReviewCycle(cycleForm.id, payload);
        alert("Cycle updated");
      } else {
        await ReviewsAPI.createReviewCycle(payload);
        alert("Cycle created");
      }
      setShowCycleForm(false);
      setCycleForm({
        id: null,
        name: "",
        review_type: "quarterly",
        description: "",
        start_date: "",
        end_date: "",
        self_review_deadline: "",
        manager_review_deadline: "",
        peer_review_deadline: "",
        status: "draft",
        participants: [],
      });
      await loadAll();
    } catch (err) {
      console.error("create/edit cycle error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  function openEditCycle(cycle) {
    setCycleForm({
      id: cycle.id,
      name: cycle.name || "",
      review_type: cycle.review_type || "quarterly",
      description: cycle.description || "",
      start_date: cycle.start_date ? cycle.start_date.slice(0,10) : "",
      end_date: cycle.end_date ? cycle.end_date.slice(0,10) : "",
      self_review_deadline: cycle.self_review_deadline ? cycle.self_review_deadline.slice(0,10) : "",
      manager_review_deadline: cycle.manager_review_deadline ? cycle.manager_review_deadline.slice(0,10) : "",
      peer_review_deadline: cycle.peer_review_deadline ? cycle.peer_review_deadline.slice(0,10) : "",
      status: cycle.status || "draft",
      participants: Array.isArray(cycle.participants) ? cycle.participants : (cycle.participant_ids || []),
    });
    setShowCycleForm(true);
  }

  async function deleteCycle(id) {
    if (!(isAdmin || isHR)) return alert("Only Admin/HR can delete cycles");
    if (!window.confirm("Delete this review cycle?")) return;
    setLoading(true);
    try {
      await ReviewsAPI.deleteReviewCycle(id);
      alert("Cycle deleted");
      await loadAll();
    } catch (err) {
      console.error("delete cycle error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  async function activateCycle(id) {
    if (!(isAdmin || isHR)) return alert("Only Admin/HR");
    if (!window.confirm("Activate cycle?")) return;
    setLoading(true);
    try {
      await ReviewsAPI.activateReviewCycle(id);
      alert("Activated");
      await loadAll();
    } catch (err) {
      console.error("activate error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  async function completeCycle(id) {
    if (!(isAdmin || isHR)) return alert("Only Admin/HR");
    if (!window.confirm("Complete cycle?")) return;
    setLoading(true);
    try {
      await ReviewsAPI.completeReviewCycle(id);
      alert("Cycle completed");
      await loadAll();
    } catch (err) {
      console.error("complete error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  /* ---------------- create review ---------------- */

  function validateCreateReview() {
    if (!createReviewForm.cycle || !createReviewForm.employee || !createReviewForm.reviewer) return "cycle, employee and reviewer required";
    return null;
  }

  async function submitCreateReview(e) {
    e && e.preventDefault && e.preventDefault();
    if (!(isAdmin || isHR || isManager)) return alert("Only Admin/HR/Manager can create reviews");
    const v = validateCreateReview();
    if (v) { alert(v); return; }
    setLoading(true);
    try {
      await ReviewsAPI.createReview({
        cycle: createReviewForm.cycle,
        employee: createReviewForm.employee,
        reviewer: createReviewForm.reviewer,
      });
      alert("Review created");
      setShowCreateReview(false);
      await loadAll();
    } catch (err) {
      console.error("create review error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  /* ---------------- Self-assessment flows ---------------- */

  async function openCreateSelf(reviewId) {
    if (!reviewId) return alert("Invalid review id");
    setLoading(true);
    try {
      const review = await ReviewsAPI.getReview(reviewId);
      if (!review) throw new Error("Review not found");
      if (!isAdmin && !isHR && Number(review.employee) !== Number(user?.id)) {
        setLoading(false);
        return alert("You can only submit self-assessment for your own review");
      }
      const cycle = await resolveCycle(review.cycle);
      if (cycle && cycle.self_review_deadline) {
        const dl = new Date(cycle.self_review_deadline);
        if (!isNaN(dl)) {
          const dlEnd = new Date(dl.getTime());
          dlEnd.setHours(23, 59, 59, 999);
          if (new Date() > dlEnd) {
            setSelfMode("view");
            setSelfNotice("Self-assessment deadline has passed for this review cycle.");
            setSelfForm({
              id: null,
              review: reviewId,
              accomplishments: "",
              challenges_faced: "",
              skills_developed: "",
              quality_of_work: 3,
              productivity: 3,
              communication: 3,
              teamwork: 3,
              initiative: 3,
              goals_achieved: "",
              goals_for_next_period: "",
              overall_rating: null,
              additional_comments: "",
              cycle_name: cycle.name || review.cycle_name || review.cycle,
              cycle_review_type: cycle.review_type || "",
              cycle_status: cycle.status || "",
              cycle_start_date: cycle.start_date || "",
              cycle_end_date: cycle.end_date || "",
              employee_name: review.employee_name || review.employee,
            });
            setShowSelfForm(true);
            return;
          }
        }
      }

      setSelfNotice("");
      setSelfMode("create");
      setSelfForm({
        id: null,
        review: reviewId,
        accomplishments: "",
        challenges_faced: "",
        skills_developed: "",
        quality_of_work: 3,
        productivity: 3,
        communication: 3,
        teamwork: 3,
        initiative: 3,
        goals_achieved: "",
        goals_for_next_period: "",
        overall_rating: null,
        additional_comments: "",
        cycle_name: (cycle && (cycle.name)) || review.cycle_name || review.cycle,
        cycle_review_type: cycle?.review_type || "",
        cycle_status: cycle?.status || "",
        cycle_start_date: cycle?.start_date || "",
        cycle_end_date: cycle?.end_date || "",
        employee_name: review.employee_name || review.employee,
      });
      setShowSelfForm(true);
    } catch (err) {
      console.error("openCreateSelf error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  async function openViewSelf(selfIdOrObj) {
    setLoading(true);
    try {
      const id = (typeof selfIdOrObj === "object" && selfIdOrObj !== null) ? (selfIdOrObj.id ?? selfIdOrObj) : selfIdOrObj;
      const idNum = Number(id);
      if (!Number.isFinite(idNum)) throw new Error("Invalid self-assessment id");

      const data = await ReviewsAPI.getSelfAssessment(idNum);
      setSelfForm({
        id: data.id,
        review: data.review,
        accomplishments: data.accomplishments || "",
        challenges_faced: data.challenges_faced || "",
        skills_developed: data.skills_developed || "",
        quality_of_work: data.quality_of_work ?? 3,
        productivity: data.productivity ?? 3,
        communication: data.communication ?? 3,
        teamwork: data.teamwork ?? 3,
        initiative: data.initiative ?? 3,
        goals_achieved: data.goals_achieved || "",
        goals_for_next_period: data.goals_for_next_period || "",
        overall_rating: data.overall_rating ?? null,
        additional_comments: data.additional_comments || "",
        employee_name: data.employee_name || data.employee,
        cycle_name: data.cycle_name || data.cycle,
      });
      setSelfMode("view");
      setShowSelfForm(true);
    } catch (err) {
      console.error("get self-assessment error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  async function openEditSelf(selfIdOrObj) {
    setLoading(true);
    try {
      const id = (typeof selfIdOrObj === "object" && selfIdOrObj !== null) ? (selfIdOrObj.id ?? selfIdOrObj) : selfIdOrObj;
      const idNum = Number(id);
      if (!Number.isFinite(idNum)) throw new Error("Invalid self-assessment id");

      const data = await ReviewsAPI.getSelfAssessment(idNum);
      if (!data) throw new Error("Self-assessment not found");
      const review = await ReviewsAPI.getReview(data.review);
      if (!isAdmin && !isHR && Number(review.employee) !== Number(user?.id)) {
        setLoading(false);
        return alert("You can only edit your own self-assessment");
      }
      const cycle = await resolveCycle(review.cycle);
      if (cycle && cycle.self_review_deadline) {
        const dl = new Date(cycle.self_review_deadline);
        if (!isNaN(dl)) {
          const dlEnd = new Date(dl.getTime());
          dlEnd.setHours(23, 59, 59, 999);
          if (new Date() > dlEnd) {
            setLoading(false);
            return alert("Self-assessment deadline has passed for this review cycle; editing is not allowed");
          }
        }
      }

      setSelfForm({
        id: data.id,
        review: data.review,
        accomplishments: data.accomplishments || "",
        challenges_faced: data.challenges_faced || "",
        skills_developed: data.skills_developed || "",
        quality_of_work: data.quality_of_work ?? 3,
        productivity: data.productivity ?? 3,
        communication: data.communication ?? 3,
        teamwork: data.teamwork ?? 3,
        initiative: data.initiative ?? 3,
        goals_achieved: data.goals_achieved || "",
        goals_for_next_period: data.goals_for_next_period || "",
        overall_rating: data.overall_rating ?? null,
        additional_comments: data.additional_comments || "",
      });
      setSelfMode("edit");
      setShowSelfForm(true);
    } catch (err) {
      console.error("openEditSelf error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  function validateSelf() {
    const required = ["review", "accomplishments", "challenges_faced", "skills_developed", "goals_achieved", "goals_for_next_period"];
    const missing = required.filter(k => !selfForm[k] || String(selfForm[k]).trim() === "");
    if (missing.length) return `Missing: ${missing.join(", ")}`;
    return null;
  }

  async function submitSelf(e) {
    e && e.preventDefault && e.preventDefault();
    if (selfMode === "create" && !(isEmployee || isIntern)) return alert("Only employee/intern can submit self-assessment");
    if (selfMode === "edit" && !(isEmployee || isIntern || isAdmin)) return alert("Only employee or admin can edit self-assessment");
    const v = validateSelf();
    if (v) { alert(v); return; }

    setLoading(true);
    try {
      const reviewId = Number(selfForm.review);
      if (!Number.isFinite(reviewId)) throw new Error("Review id must be a number");
      const review = await ReviewsAPI.getReview(reviewId);
      if (!review) throw new Error("Review not found");
      if (!isAdmin && !isHR && Number(review.employee) !== Number(user?.id)) {
        setLoading(false);
        return alert("You can only submit self-assessment for your own review");
      }
      const cycle = await resolveCycle(review.cycle);
      if (cycle && cycle.self_review_deadline) {
        const dl = new Date(cycle.self_review_deadline);
        if (!isNaN(dl)) {
          const dlEnd = new Date(dl.getTime());
          dlEnd.setHours(23, 59, 59, 999);
          if (new Date() > dlEnd) {
            setLoading(false);
            return alert("Self-assessment deadline has passed for this review cycle");
          }
        }
      }

      const q = Number(selfForm.quality_of_work) || 0;
      const p = Number(selfForm.productivity) || 0;
      const comm = Number(selfForm.communication) || 0;
      const team = Number(selfForm.teamwork) || 0;
      const init = Number(selfForm.initiative) || 0;
      const comps = [q, p, comm, team, init].filter(n => Number.isFinite(n) && n > 0);
      const avg = comps.length > 0 ? parseFloat((comps.reduce((s, x) => s + x, 0) / comps.length).toFixed(2)) : null;

      const payload = {
        review: reviewId,
        accomplishments: selfForm.accomplishments,
        challenges_faced: selfForm.challenges_faced,
        skills_developed: selfForm.skills_developed,
        quality_of_work: Number(selfForm.quality_of_work) || 3,
        productivity: Number(selfForm.productivity) || 3,
        communication: Number(selfForm.communication) || 3,
        teamwork: Number(selfForm.teamwork) || 3,
        initiative: Number(selfForm.initiative) || 3,
        goals_achieved: selfForm.goals_achieved,
        goals_for_next_period: selfForm.goals_for_next_period,
        overall_rating: (selfForm.overall_rating !== null && selfForm.overall_rating !== undefined && selfForm.overall_rating !== "") ? Number(selfForm.overall_rating) : (avg !== null ? avg : undefined),
        additional_comments: selfForm.additional_comments || "",
      };

      if (payload.overall_rating === undefined) payload.overall_rating = avg !== null ? avg : 3;

      if (selfForm.id) {
        await ReviewsAPI.patchSelfAssessment(selfForm.id, payload);
        alert("Self-assessment updated");
      } else {
        await ReviewsAPI.createSelfAssessment(payload);
        alert("Self-assessment submitted");
      }
      setShowSelfForm(false);
      setSelfMode("create");
      setSelfForm({
        id: null,
        review: "",
        accomplishments: "",
        challenges_faced: "",
        skills_developed: "",
        quality_of_work: 3,
        productivity: 3,
        communication: 3,
        teamwork: 3,
        initiative: 3,
        goals_achieved: "",
        goals_for_next_period: "",
        overall_rating: null,
        additional_comments: ""
      });
      await loadAll();
    } catch (err) {
      console.error("self assessment error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  async function deleteSelf(selfId) {
    if (!(isAdmin || isHR)) return alert("Only Admin/HR can delete self-assessments");
    if (!window.confirm("Delete this self-assessment? This cannot be undone.")) return;
    setLoading(true);
    try {
      await ReviewsAPI.deleteSelfAssessment(selfId);
      alert("Self-assessment deleted");
      await loadAll();
    } catch (err) {
      console.error("delete self-assessment error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  /* ---------------- Manager review flows ---------------- */

  function openCreateManager(reviewId = "") {
    setManagerMode("create");
    setManagerForm({
      id: null, review: reviewId, performance_summary: "", strengths: "",
      areas_for_improvement: "", quality_of_work: 3, productivity: 3, communication: 3,
      teamwork: 3, initiative: 3, leadership: 3, problem_solving: 3,
      goals_achievement_comment: "", goals_for_next_period: "", promotion_recommendation: false,
      salary_increase_recommendation: false, training_recommendations: "", overall_rating: null, manager_comments: ""
    });
    setShowManagerForm(true);
  }

  async function openViewManager(id) {
    setLoading(true);
    try {
      const d = await ReviewsAPI.getManagerReview(id);
      setManagerForm({
        id: d.id, review: d.review, performance_summary: d.performance_summary || "", strengths: d.strengths || "",
        areas_for_improvement: d.areas_for_improvement || "", quality_of_work: d.quality_of_work ?? 3,
        productivity: d.productivity ?? 3, communication: d.communication ?? 3, teamwork: d.teamwork ?? 3,
        initiative: d.initiative ?? 3, leadership: d.leadership ?? 3, problem_solving: d.problem_solving ?? 3,
        goals_achievement_comment: d.goals_achievement_comment || "", goals_for_next_period: d.goals_for_next_period || "",
        promotion_recommendation: Boolean(d.promotion_recommendation), salary_increase_recommendation: Boolean(d.salary_increase_recommendation),
        training_recommendations: d.training_recommendations || "", overall_rating: d.overall_rating ?? null, manager_comments: d.manager_comments || ""
      });
      setManagerMode("view");
      setShowManagerForm(true);
    } catch (err) {
      console.error("get manager review error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  async function openEditManager(id) {
    setLoading(true);
    try {
      const d = await ReviewsAPI.getManagerReview(id);
      setManagerForm({
        id: d.id, review: d.review, performance_summary: d.performance_summary || "", strengths: d.strengths || "",
        areas_for_improvement: d.areas_for_improvement || "", quality_of_work: d.quality_of_work ?? 3,
        productivity: d.productivity ?? 3, communication: d.communication ?? 3, teamwork: d.teamwork ?? 3,
        initiative: d.initiative ?? 3, leadership: d.leadership ?? 3, problem_solving: d.problem_solving ?? 3,
        goals_achievement_comment: d.goals_achievement_comment || "", goals_for_next_period: d.goals_for_next_period || "",
        promotion_recommendation: Boolean(d.promotion_recommendation), salary_increase_recommendation: Boolean(d.salary_increase_recommendation),
        training_recommendations: d.training_recommendations || "", overall_rating: d.overall_rating ?? null, manager_comments: d.manager_comments || ""
      });
      setManagerMode("edit");
      setShowManagerForm(true);
    } catch (err) {
      console.error("get manager review error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  function validateManager() {
    if (!managerForm.review || !managerForm.performance_summary) return "review and performance_summary required";
    if (!String(managerForm.goals_achievement_comment || "").trim()) return "goals_achievement_comment required";
    if (!String(managerForm.goals_for_next_period || "").trim()) return "goals_for_next_period required";
    return null;
  }

  // === submitManager with robust inclusive deadline check (end of day) ===
  async function submitManager(e) {
    e && e.preventDefault && e.preventDefault();
    if (!(isManager || isAdmin)) return alert("Only Manager or Admin can create/edit manager reviews");
    const v = validateManager();
    if (v) return alert(v);

    setLoading(true);
    try {
      const payload = {};
      const reviewId = Number(managerForm.review);
      if (!Number.isFinite(reviewId)) throw new Error("Review id must be a number");
      payload.review = reviewId;

      // Always include these text fields (backend may require them)
      payload.performance_summary = String(managerForm.performance_summary || "").trim();
      payload.strengths = String(managerForm.strengths || "").trim();
      payload.areas_for_improvement = String(managerForm.areas_for_improvement || "").trim();
      payload.goals_achievement_comment = String(managerForm.goals_achievement_comment || "").trim();
      payload.goals_for_next_period = String(managerForm.goals_for_next_period || "").trim();
      payload.training_recommendations = String(managerForm.training_recommendations || "").trim();
      payload.manager_comments = String(managerForm.manager_comments || "").trim();

      const numericFields = ["quality_of_work","productivity","communication","teamwork","initiative","leadership","problem_solving"];
      numericFields.forEach(k => {
        const n = Number(managerForm[k]);
        if (Number.isFinite(n)) payload[k] = n;
      });

      const overallNum = Number(managerForm.overall_rating);
      if (Number.isFinite(overallNum)) payload.overall_rating = overallNum;
      else {
        const nums = numericFields.map(k => Number(managerForm[k])).filter(n => Number.isFinite(n));
        if (nums.length > 0) payload.overall_rating = parseFloat((nums.reduce((s,x)=>s+x,0)/nums.length).toFixed(2));
        else { setLoading(false); return alert("overall_rating is required (or fill competency ratings)"); }
      }

      payload.promotion_recommendation = Boolean(managerForm.promotion_recommendation);
      payload.salary_increase_recommendation = Boolean(managerForm.salary_increase_recommendation);

      // --- Robust deadline check: treat deadline date as end of day (inclusive) ---
      const reviewObj = await ReviewsAPI.getReview(reviewId);
      if (reviewObj) {
        const cyc = await resolveCycle(reviewObj.cycle);
        if (cyc && cyc.manager_review_deadline) {
          const dlRaw = cyc.manager_review_deadline;
          const dl = new Date(dlRaw);
          if (!isNaN(dl)) {
            const dlEnd = new Date(dl.getTime());
            dlEnd.setHours(23, 59, 59, 999);
            if (new Date() > dlEnd) {
              setLoading(false);
              return alert("Manager review deadline has passed for this review cycle");
            }
          }
        }
      }

      if (managerForm.id) {
        await ReviewsAPI.patchManagerReview(managerForm.id, payload);
        alert("Manager review updated");
      } else {
        const reviewExists = managerReviews.some(m => Number(m.review) === reviewId);
        if (reviewExists) {
          setLoading(false);
          return alert("manager review with this review already exists.");
        }
        await ReviewsAPI.createManagerReview(payload);
        alert("Manager review created");
      }

      setShowManagerForm(false);
      setManagerMode("create");
      setManagerForm({
        id: null, review: "", performance_summary: "", strengths: "", areas_for_improvement: "",
        quality_of_work: 3, productivity: 3, communication: 3, teamwork: 3, initiative: 3,
        leadership: 3, problem_solving: 3, goals_achievement_comment: "", goals_for_next_period: "",
        promotion_recommendation: false, salary_increase_recommendation: false, training_recommendations: "",
        overall_rating: null, manager_comments: ""
      });
      await loadAll();
    } catch (err) {
      console.error("manager review error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  async function deleteManager(id) {
    if (!(isAdmin || isHR)) return alert("Only Admin/HR can delete manager reviews");
    if (!window.confirm("Delete this manager review?")) return;
    setLoading(true);
    try {
      await ReviewsAPI.deleteManagerReview(id);
      alert("Manager review deleted");
      await loadAll();
    } catch (err) {
      console.error("delete manager review error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  /* ---------------- peer feedback ---------------- */

  async function openPeerForReview(reviewId) {
    if (!reviewId) return alert("Invalid review id");
    setLoading(true);
    try {
      const review = await ReviewsAPI.getReview(reviewId);
      if (!review) throw new Error("Review not found");
      if (Number(review.employee) === Number(user?.id)) {
        setLoading(false);
        return alert("You cannot provide peer feedback for your own review.");
      }
      const cycle = await resolveCycle(review.cycle);
      if (cycle && cycle.peer_review_deadline) {
        const dl = new Date(cycle.peer_review_deadline);
        if (!isNaN(dl)) {
          const dlEnd = new Date(dl.getTime());
          dlEnd.setHours(23, 59, 59, 999);
          if (new Date() > dlEnd) {
            setLoading(false);
            return alert("Peer review deadline has passed for this review cycle");
          }
        }
      }
      setPeerForm(p => ({ ...p, review: reviewId }));
      setShowPeerForm(true);
    } catch (err) {
      console.error("openPeerForReview error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  function validatePeer() {
    if (!peerForm.review || !peerForm.collaboration_feedback) return "review and collaboration_feedback required";
    return null;
  }

  async function submitPeer(e) {
    e && e.preventDefault && e.preventDefault();
    const v = validatePeer();
    if (v) return alert(v);
    setLoading(true);
    try {
      const reviewId = Number(peerForm.review);
      console.log('[Peer Feedback] Submitting for review ID:', reviewId);
      console.log('[Peer Feedback] Current user ID:', user?.id);
      
      if (!Number.isFinite(reviewId)) throw new Error("Review ID must be a number");
      
      const review = await ReviewsAPI.getReview(reviewId);
      console.log('[Peer Feedback] Fetched review:', review);
      
      if (!review) throw new Error("Review not found");
      
      console.log('[Peer Feedback] Review employee ID:', review.employee);
      console.log('[Peer Feedback] Comparison:', Number(review.employee), 'vs', Number(user?.id));
      
      if (Number(review.employee) === Number(user?.id)) {
        setLoading(false);
        return alert("You cannot provide peer feedback for your own review.");
      }
      const cycle = await resolveCycle(review.cycle);
      if (cycle && cycle.peer_review_deadline) {
        const dl = new Date(cycle.peer_review_deadline);
        if (!isNaN(dl)) {
          const dlEnd = new Date(dl.getTime());
          dlEnd.setHours(23, 59, 59, 999);
          if (new Date() > dlEnd) {
            setLoading(false);
            return alert("Peer review deadline has passed for this review cycle");
          }
        }
      }

      const payload = {
        review: reviewId,
        collaboration_feedback: peerForm.collaboration_feedback,
        strengths: peerForm.strengths || "",
        areas_for_improvement: peerForm.areas_for_improvement || "",
        teamwork: Number(peerForm.teamwork) || 3,
        communication: Number(peerForm.communication) || 3,
        reliability: Number(peerForm.reliability) || 3,
        helpfulness: Number(peerForm.helpfulness) || 3,
        overall_rating: Number(peerForm.overall_rating) || 3,
        additional_comments: peerForm.additional_comments || "",
        is_anonymous: Boolean(peerForm.is_anonymous),
      };

      console.log('[Peer Feedback] Payload:', payload);
      await ReviewsAPI.createPeerFeedback(payload);
      alert("Peer feedback submitted");
      setShowPeerForm(false);
      setPeerForm({
        review: "", collaboration_feedback: "", strengths: "", areas_for_improvement: "",
        teamwork: 3, communication: 3, reliability: 3, helpfulness: 3, overall_rating: 3,
        additional_comments: "", is_anonymous: false
      });
      await loadAll();
    } catch (err) {
      console.error("[Peer Feedback] Error:", err);
      console.error("[Peer Feedback] Error body:", err.body);
      console.error("[Peer Feedback] Error message:", err.message);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  /* ---------------- calculate rating ---------------- */

  async function calculateOverall(reviewId) {
    setLoading(true);
    try {
      await ReviewsAPI.calculateRating(reviewId);
      alert("Overall rating calculated");
      await loadAll();
    } catch (err) {
      console.error("calculate error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  /* ---------------- cycle stats modal ---------------- */

  async function openCycleStats(cycleId) {
    if (!cycleId) return alert("Invalid cycle id");
    setLoading(true);
    try {
      const s = await ReviewsAPI.getCycleStatistics(cycleId);
      setStatsData(s);
      setShowStatsModal(true);
    } catch (err) {
      console.error("get cycle stats error", err);
      alert(formatServerError(err));
    } finally { setLoading(false); }
  }

  /* ---------------- UI render ---------------- */
  return (
    <div className="container py-4">
      <style>{`
        .hero { background: linear-gradient(90deg, rgba(13,110,253,0.04), rgba(13,110,253,0)); padding:12px;border-radius:8px; }
        .card-head { display:flex; justify-content:space-between; align-items:center; }
        .readonly { background: #f8f9fa; }
        pre.stats { background:#f8f9fa; padding:10px; border-radius:6px; max-height:300px; overflow:auto; }
      `}</style>

      <div className="hero mb-3 d-flex justify-content-between align-items-center">
        <div>
          <h4 className="mb-0">Reviews</h4>
          <div className="small text-muted">Role: {role}</div>
        </div>
        <div className="d-flex gap-2">
          {(isAdmin || isHR) && <button type="button" className="btn btn-sm btn-outline-primary" onClick={() => {
            setCycleForm({ id: null, name: "", review_type: "quarterly", description: "", start_date: "", end_date: "", self_review_deadline: "", manager_review_deadline: "", peer_review_deadline: "", status: "draft", participants: [] });
            setShowCycleForm(true);
          }}>+ New Cycle</button>}
          {(isAdmin || isHR || isManager) && <button type="button" className="btn btn-sm btn-outline-success" onClick={() => setShowCreateReview(true)}>+ Create Review</button>}
          {(isManager || isAdmin || isHR) && <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => openCreateManager()}>+ Manager Review</button>}
          {(isEmployee || isIntern) && <button type="button" className="btn btn-sm btn-primary" onClick={() => { setSelfMode("create"); setSelfForm(p => ({ ...p, review: "" })); setShowSelfForm(true); }}>+ Self Assessment</button>}
          {(isEmployee || isIntern) && <button type="button" className="btn btn-sm btn-secondary" onClick={() => { setPeerForm({ review: "", collaboration_feedback: "", strengths: "", areas_for_improvement: "", teamwork: 3, communication: 3, reliability: 3, helpfulness: 3, overall_rating: 3, additional_comments: "", is_anonymous: false }); setShowPeerForm(true); }}>+ Peer Feedback</button>}
        </div>
      </div>

      {loading && <div className="alert alert-info">Loading...</div>}

      <div className="row">
        <div className="col-lg-4">
          {/* Cycles */}
          <div className="card mb-3">
            <div className="card-body">
              <div className="card-head"><strong>Cycles</strong><small className="text-muted">{cycles.length}</small></div>
              {cycles.length === 0 && <div className="text-muted">No cycles</div>}
              {cycles.map(c => (
                <div key={c.id} className="p-2 mb-2 border rounded">
                  <div className="d-flex justify-content-between">
                    <div>
                      <div className="fw-semibold">{c.name}</div>
                      <div className="small text-muted">{c.review_type} • {c.status}</div>
                      <div className="small text-muted">
                        <button type="button" className="btn btn-link p-0 small" onClick={() => openCycleDetails(c)}>
                          Start: {simpleDate(c.start_date)} End: {simpleDate(c.end_date)}
                        </button>
                      </div>
                    </div>
                    <div className="text-end">
                      {(isAdmin || isHR) && c.status === "draft" && <button type="button" className="btn btn-sm btn-outline-primary mb-1" onClick={() => activateCycle(c.id)}>Activate</button>}
                      {(isAdmin || isHR) && c.status === "active" && <button type="button" className="btn btn-sm btn-outline-success mb-1" onClick={() => completeCycle(c.id)}>Complete</button>}
                      <div className="d-flex flex-column align-items-end">
                        {(isAdmin || isHR) && <div className="d-flex gap-1">
                          <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => openEditCycle(c)}>Edit</button>
                          <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => deleteCycle(c.id)}>Delete</button>
                        </div>}
                        <button type="button" className="btn btn-sm btn-link mt-1" onClick={() => openCycleStats(c.id)}>Stats</button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Pending */}
          <div className="card mb-3">
            <div className="card-body">
              <div className="card-head"><strong>Pending</strong><small className="text-muted">{pending.length}</small></div>
              {pending.length === 0 && <div className="text-muted">No pending reviews</div>}
              {pending.map(r => (
                <div key={r.id} className="p-2 mb-2 border rounded d-flex justify-content-between">
                  <div>
                    <div className="fw-semibold">{r.employee_name || r.employee}</div>
                    <div className="small text-muted">{r.cycle_name || r.cycle} • {r.status}</div>
                  </div>
                  <div>
                    {(isAdmin || isHR || (isManager && r.reviewer === user?.id)) && <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => calculateOverall(r.id)}>Calc</button>}
                    {(isEmployee || isIntern) && Number(r.employee) !== Number(user?.id) ? (
                      <button type="button" className="btn btn-sm btn-outline-primary ms-1" onClick={() => openPeerForReview(r.id)}>Give Peer</button>
                    ) : (isEmployee || isIntern) ? (
                      <button type="button" className="btn btn-sm btn-outline-primary ms-1" disabled title="You cannot provide feedback for your own review">Give Peer</button>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col-lg-8">
          {/* My Reviews */}
          <div className="card mb-3">
            <div className="card-body">
              <div className="card-head"><strong>My Reviews</strong><small className="text-muted">{myReviews.length}</small></div>
              {myReviews.length === 0 && <div className="text-muted">No reviews</div>}
              {myReviews.map(r => {
                const selfDeadlinePassed = deadlinePassedForReviewCached(r);
                return (
                  <div key={r.id} className="p-2 mb-2 border rounded d-flex justify-content-between">
                    <div>
                      <div className="fw-semibold">{r.cycle_name || r.cycle} — {r.employee_name || r.employee}</div>
                      <div className="small text-muted">Status: {r.status} • Rating: {r.overall_rating ?? "-"}</div>
                    </div>
                    <div className="d-flex flex-column">
                      {(isEmployee || isIntern) && !r.self_assessment && (
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-success mb-1"
                          onClick={() => openCreateSelf(r.id)}
                          disabled={selfDeadlinePassed}
                          title={selfDeadlinePassed ? "Self-assessment deadline has passed" : "Submit self-assessment"}
                        >
                          Submit Self
                        </button>
                      )}
                      {r.self_assessment && (
                        <>
                          <button type="button" className="btn btn-sm btn-outline-secondary mb-1" onClick={() => openViewSelf(r.self_assessment)}>View Self</button>
                          {((isEmployee && r.employee === user?.id) || isAdmin) && <button type="button" className="btn btn-sm btn-outline-primary mb-1" onClick={() => openEditSelf(r.self_assessment)}>Edit Self</button>}
                          {(isAdmin || isHR) && <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => deleteSelf(r.self_assessment)}>Delete Self</button>}
                        </>
                      )}

                      {(isEmployee || isIntern) && Number(r.employee) !== Number(user?.id) ? (
                        <button type="button" className="btn btn-sm btn-outline-secondary mt-1" onClick={() => openPeerForReview(r.id)}>Give Peer</button>
                      ) : (isEmployee || isIntern) ? (
                        <button type="button" className="btn btn-sm btn-outline-secondary mt-1" disabled title="You cannot provide feedback for your own review">Give Peer</button>
                      ) : null}

                      {(isManager && r.reviewer === user?.id) && <button type="button" className="btn btn-sm btn-outline-primary mt-1" onClick={() => calculateOverall(r.id)}>Calc</button>}
                      {(isAdmin || isHR) && <button type="button" className="btn btn-sm btn-outline-danger mt-1" onClick={async ()=> {
                        if (!window.confirm("Delete this review?")) return;
                        try { await ReviewsAPI.deleteReview(r.id); alert("Deleted"); await loadAll(); } catch(e) { alert(formatServerError(e)); }
                      }}>Delete</button>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Self Assessments */}
          <div className="card mb-3">
            <div className="card-body">
              <div className="card-head"><strong>Self Assessments</strong><small className="text-muted">{selfAssessments.length}</small></div>
              {selfAssessments.length === 0 && <div className="text-muted">No self-assessments</div>}
              {selfAssessments.map(s => (
                <div key={s.id} className="p-2 mb-2 border rounded d-flex justify-content-between">
                  <div>
                    <div className="fw-semibold">{s.employee_name || s.employee} — {s.cycle_name || s.cycle}</div>
                    <div className="small text-muted">Overall: {s.overall_rating ?? "-"} • Created: {s.created_at ? simpleDate(s.created_at) : "-"}</div>
                    <div className="small text-truncate" style={{maxWidth:400}}>{s.accomplishments ? (s.accomplishments.length > 140 ? s.accomplishments.slice(0,140) + "..." : s.accomplishments) : ""}</div>
                  </div>
                  <div className="d-flex flex-column">
                    <button type="button" className="btn btn-sm btn-outline-secondary mb-1" onClick={() => openViewSelf(s.id)}>View</button>
                    {((isEmployee && s.employee === user?.id) || isAdmin) && <button type="button" className="btn btn-sm btn-outline-primary mb-1" onClick={() => openEditSelf(s.id)}>Edit</button>}
                    {(isAdmin || isHR) && <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => deleteSelf(s.id)}>Delete</button>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Manager Reviews */}
          {(isManager || isAdmin || isHR) && (
            <div className="card mb-3">
              <div className="card-body">
                <div className="card-head"><strong>Manager Reviews</strong><small className="text-muted">{managerReviews.length}</small></div>
                {managerReviews.length === 0 && <div className="text-muted">No manager reviews</div>}
                {managerReviews.map(m => (
                  <div key={m.id} className="p-2 mb-2 border rounded d-flex justify-content-between">
                    <div>
                      <div className="fw-semibold">Review: {m.review} — {m.employee_name || m.employee}</div>
                      <div className="small text-muted">Rating: {m.overall_rating ?? "-"}</div>
                    </div>
                    <div className="d-flex gap-1">
                      <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => openViewManager(m.id)}>View</button>
                      {(isManager || isAdmin) && <button type="button" className="btn btn-sm btn-outline-primary" onClick={() => openEditManager(m.id)}>Edit</button>}
                      {(isAdmin || isHR) && <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => deleteManager(m.id)}>Delete</button>}
                    </div>
                  </div>
                ))}
                {(isManager || isAdmin) && <div className="mt-2"><button type="button" className="btn btn-sm btn-success" onClick={() => openCreateManager()}>+ New Manager Review</button></div>}
              </div>
            </div>
          )}

          {/* All Reviews (admin/hr) */}
          {(isAdmin || isHR) && (
            <div className="card mb-3">
              <div className="card-body">
                <div className="card-head"><strong>All Reviews</strong><small className="text-muted">{allReviews.length}</small></div>
                {allReviews.length === 0 && <div className="text-muted">No reviews</div>}
                {allReviews.map(r => (
                  <div key={r.id} className="p-2 mb-2 border rounded d-flex justify-content-between">
                    <div>
                      <div className="fw-semibold">{r.employee_name || r.employee}</div>
                      <div className="small text-muted">Cycle: {r.cycle_name || r.cycle} • Status: {r.status}</div>
                    </div>
                    <div><button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => calculateOverall(r.id)}>Calc</button></div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ------------- Modal forms ------------- */}

      {/* Cycle Form */}
      <div className={`modal ${showCycleForm ? "d-block" : ""}`} tabIndex={-1} style={{ background: showCycleForm ? "rgba(0,0,0,0.45)" : undefined }}>
        <div className="modal-dialog">
          <form className="modal-content" onSubmit={submitCycle}>
            <div className="modal-header"><h5 className="modal-title">{cycleForm.id ? "Edit Cycle" : "Create Cycle"}</h5><button type="button" className="btn-close" onClick={() => setShowCycleForm(false)} /></div>
            <div className="modal-body">
              <div className="mb-2"><label className="form-label">Name</label><input className="form-control" value={cycleForm.name} onChange={e => setCycleForm(p => ({ ...p, name: e.target.value }))} required /></div>
              <div className="mb-2"><label className="form-label">Type</label>
                <select className="form-select" value={cycleForm.review_type} onChange={e => setCycleForm(p => ({ ...p, review_type: e.target.value }))}>
                  <option value="quarterly">quarterly</option>
                  <option value="semi_annual">semi_annual</option>
                  <option value="annual">annual</option>
                  <option value="probation">probation</option>
                </select>
              </div>
              <div className="row g-2">
                <div className="col-md-6 mb-2"><label className="form-label">Start</label><input type="date" className="form-control" value={cycleForm.start_date} onChange={e => setCycleForm(p => ({ ...p, start_date: e.target.value }))} required /></div>
                <div className="col-md-6 mb-2"><label className="form-label">End</label><input type="date" className="form-control" value={cycleForm.end_date} onChange={e => setCycleForm(p => ({ ...p, end_date: e.target.value }))} required /></div>
              </div>
              <div className="row g-2">
                <div className="col-md-6 mb-2"><label className="form-label">Self review deadline</label><input type="date" className="form-control" value={cycleForm.self_review_deadline} onChange={e => setCycleForm(p => ({ ...p, self_review_deadline: e.target.value }))} required /></div>
                <div className="col-md-6 mb-2"><label className="form-label">Manager review deadline</label><input type="date" className="form-control" value={cycleForm.manager_review_deadline} onChange={e => setCycleForm(p => ({ ...p, manager_review_deadline: e.target.value }))} required /></div>
              </div>
              <div className="mb-2"><label className="form-label">Peer review deadline (optional)</label><input type="date" className="form-control" value={cycleForm.peer_review_deadline} onChange={e => setCycleForm(p => ({ ...p, peer_review_deadline: e.target.value }))} /></div>
              <div className="mb-2"><label className="form-label">Participants (IDs comma separated)</label><input className="form-control" value={cycleForm.participants.join(",")} onChange={e => setCycleForm(p => ({ ...p, participants: e.target.value.split(",").map(s=>s.trim()).filter(Boolean).map(Number) }))} placeholder="e.g. 1,2,3" required /></div>
              <div className="mb-2"><label className="form-label">Status</label>
                <select className="form-select" value={cycleForm.status} onChange={e => setCycleForm(p => ({ ...p, status: e.target.value }))}>
                  <option value="draft">draft</option>
                  <option value="active">active</option>
                  <option value="completed">completed</option>
                  <option value="cancelled">cancelled</option>
                </select>
              </div>
            </div>
            <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowCycleForm(false)}>Close</button><button type="submit" className="btn btn-primary">{cycleForm.id ? "Save" : "Create"}</button></div>
          </form>
        </div>
      </div>

      {/* Create Review Form */}
      <div className={`modal ${showCreateReview ? "d-block" : ""}`} tabIndex={-1} style={{ background: showCreateReview ? "rgba(0,0,0,0.45)" : undefined }}>
        <div className="modal-dialog">
          <form className="modal-content" onSubmit={submitCreateReview}>
            <div className="modal-header"><h5 className="modal-title">Create Review</h5><button type="button" className="btn-close" onClick={() => setShowCreateReview(false)} /></div>
            <div className="modal-body">
              <div className="mb-2"><label className="form-label">Cycle ID</label><input className="form-control" value={createReviewForm.cycle} onChange={e => setCreateReviewForm(p => ({ ...p, cycle: e.target.value }))} required /></div>
              <div className="mb-2"><label className="form-label">Employee ID</label><input className="form-control" value={createReviewForm.employee} onChange={e => setCreateReviewForm(p => ({ ...p, employee: e.target.value }))} required /></div>
              <div className="mb-2"><label className="form-label">Reviewer (manager) ID</label><input className="form-control" value={createReviewForm.reviewer} onChange={e => setCreateReviewForm(p => ({ ...p, reviewer: e.target.value }))} required /></div>
              <div className="small text-muted">Backend requires unique (cycle, employee) pair; you'll see validation if duplicate.</div>
            </div>
            <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowCreateReview(false)}>Close</button><button type="submit" className="btn btn-primary">Create</button></div>
          </form>
        </div>
      </div>

      {/* Self Assessment Form */}
      <div className={`modal ${showSelfForm ? "d-block" : ""}`} tabIndex={-1} style={{ background: showSelfForm ? "rgba(0,0,0,0.45)" : undefined }}>
        <div className="modal-dialog modal-lg">
          {selfMode === "view" ? (
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">View Self Assessment</h5>
                <button type="button" className="btn-close" onClick={() => setShowSelfForm(false)} />
              </div>
              <div className="modal-body">
                {selfForm.employee_name && <div className="mb-2"><strong>Employee:</strong> {selfForm.employee_name}</div>}
                {(selfForm.cycle_review_type || selfForm.cycle_status) && (
                  <div className="mb-1 small text-muted">{selfForm.cycle_review_type} • {selfForm.cycle_status}</div>
                )}
                {(selfForm.cycle_start_date || selfForm.cycle_end_date) && (
                  <div className="mb-2 small text-muted">Start: {simpleDate(selfForm.cycle_start_date)} End: {simpleDate(selfForm.cycle_end_date)}</div>
                )}
                {selfForm.cycle_name && <div className="mb-2"><strong>Cycle:</strong> {selfForm.cycle_name}</div>}
                {selfNotice && <div className="alert alert-warning">{selfNotice}</div>}
                <div className="mb-2"><label className="form-label">Review ID</label><div className="form-control readonly">{selfForm.review}</div></div>
                <div className="mb-2"><label className="form-label">Accomplishments</label><div className="form-control readonly" style={{whiteSpace: 'pre-wrap'}}>{selfForm.accomplishments}</div></div>
                <div className="mb-2"><label className="form-label">Challenges faced</label><div className="form-control readonly" style={{whiteSpace: 'pre-wrap'}}>{selfForm.challenges_faced}</div></div>
                <div className="mb-2"><label className="form-label">Skills developed</label><div className="form-control readonly" style={{whiteSpace: 'pre-wrap'}}>{selfForm.skills_developed}</div></div>
                <div className="mb-2"><label className="form-label">Goals achieved</label><div className="form-control readonly" style={{whiteSpace: 'pre-wrap'}}>{selfForm.goals_achieved}</div></div>
                <div className="mb-2"><label className="form-label">Goals for next period</label><div className="form-control readonly" style={{whiteSpace: 'pre-wrap'}}>{selfForm.goals_for_next_period}</div></div>
                <div className="mb-2"><label className="form-label">Overall rating</label><div className="form-control readonly">{selfForm.overall_rating ?? '-'}</div></div>
                <div className="mb-2"><label className="form-label">Additional comments</label><div className="form-control readonly" style={{whiteSpace: 'pre-wrap'}}>{selfForm.additional_comments}</div></div>
              </div>
              <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowSelfForm(false)}>Close</button>{(isAdmin || isHR) && selfForm.id && <button type="button" className="btn btn-danger" onClick={() => deleteSelf(selfForm.id)}>Delete</button>}</div>
            </div>
          ) : (
            <form className="modal-content" onSubmit={submitSelf}>
              <div className="modal-header"><h5 className="modal-title">{selfMode === "edit" ? "Edit Self Assessment" : "Create Self Assessment"}</h5><button type="button" className="btn-close" onClick={() => setShowSelfForm(false)} /></div>
              <div className="modal-body">
                {selfForm.employee_name && <div className="mb-2"><strong>Employee:</strong> {selfForm.employee_name}</div>}
                {selfForm.cycle_name && <div className="mb-2"><strong>Cycle:</strong> {selfForm.cycle_name}</div>}
                {selfNotice && <div className="alert alert-warning">{selfNotice}</div>}
                <div className="mb-2"><label className="form-label">Review ID</label><input className="form-control" value={selfForm.review} onChange={e => setSelfForm(p => ({ ...p, review: e.target.value }))} required /></div>
                <div className="mb-2"><label className="form-label">Accomplishments</label><textarea className="form-control" value={selfForm.accomplishments} onChange={e => setSelfForm(p => ({ ...p, accomplishments: e.target.value }))} required /></div>
                <div className="mb-2"><label className="form-label">Challenges faced</label><textarea className="form-control" value={selfForm.challenges_faced} onChange={e => setSelfForm(p => ({ ...p, challenges_faced: e.target.value }))} required /></div>
                <div className="mb-2"><label className="form-label">Skills developed</label><textarea className="form-control" value={selfForm.skills_developed} onChange={e => setSelfForm(p => ({ ...p, skills_developed: e.target.value }))} required /></div>
                <div className="mb-2"><label className="form-label">Goals achieved</label><textarea className="form-control" value={selfForm.goals_achieved} onChange={e => setSelfForm(p => ({ ...p, goals_achieved: e.target.value }))} required /></div>
                <div className="mb-2"><label className="form-label">Goals for next period</label><textarea className="form-control" value={selfForm.goals_for_next_period} onChange={e => setSelfForm(p => ({ ...p, goals_for_next_period: e.target.value }))} required /></div>
                <div className="mb-2"><label className="form-label">Quality of work (1-5)</label><input type="number" min="1" max="5" className="form-control" value={selfForm.quality_of_work} onChange={e => setSelfForm(p => ({ ...p, quality_of_work: Number(e.target.value) }))} /></div>
                <div className="mb-2"><label className="form-label">Productivity (1-5)</label><input type="number" min="1" max="5" className="form-control" value={selfForm.productivity} onChange={e => setSelfForm(p => ({ ...p, productivity: Number(e.target.value) }))} /></div>
                <div className="mb-2"><label className="form-label">Communication (1-5)</label><input type="number" min="1" max="5" className="form-control" value={selfForm.communication} onChange={e => setSelfForm(p => ({ ...p, communication: Number(e.target.value) }))} /></div>
                <div className="mb-2"><label className="form-label">Teamwork (1-5)</label><input type="number" min="1" max="5" className="form-control" value={selfForm.teamwork} onChange={e => setSelfForm(p => ({ ...p, teamwork: Number(e.target.value) }))} /></div>
                <div className="mb-2"><label className="form-label">Initiative (1-5)</label><input type="number" min="1" max="5" className="form-control" value={selfForm.initiative} onChange={e => setSelfForm(p => ({ ...p, initiative: Number(e.target.value) }))} /></div>
                <div className="mb-2"><label className="form-label">Overall rating (optional)</label><input type="number" step="0.01" min="1" max="5" className="form-control" value={selfForm.overall_rating ?? ""} onChange={e => setSelfForm(p => ({ ...p, overall_rating: e.target.value === "" ? null : Number(e.target.value) }))} /></div>
                <div className="mb-2"><label className="form-label">Additional comments</label><textarea className="form-control" value={selfForm.additional_comments} onChange={e => setSelfForm(p => ({ ...p, additional_comments: e.target.value }))} /></div>
              </div>
              <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowSelfForm(false)}>Close</button><button type="submit" className="btn btn-primary">{selfMode === "edit" ? "Save" : "Submit"}</button></div>
            </form>
          )}
        </div>
      </div>

      {/* Peer Feedback Form */}
      <div className={`modal ${showPeerForm ? "d-block" : ""}`} tabIndex={-1} style={{ background: showPeerForm ? "rgba(0,0,0,0.45)" : undefined }}>
        <div className="modal-dialog modal-lg">
          <form className="modal-content" onSubmit={submitPeer}>
            <div className="modal-header"><h5 className="modal-title">Peer Feedback</h5><button type="button" className="btn-close" onClick={() => setShowPeerForm(false)} /></div>
            <div className="modal-body">
              <div className="mb-2">
                <label className="form-label">Select Review (Employee to give feedback for)</label>
                {allReviews.filter(r => Number(r.employee) !== Number(user?.id)).length === 0 ? (
                  <div className="alert alert-warning">
                    <strong>No reviews available for peer feedback</strong>
                    <p className="mb-0 small">There are no other employees' reviews in the system yet. Reviews must be created for other employees before you can provide peer feedback.</p>
                  </div>
                ) : (
                  <select 
                    className="form-select" 
                    value={peerForm.review} 
                    onChange={e => setPeerForm(p => ({ ...p, review: e.target.value }))} 
                    required
                  >
                    <option value="">-- Select a review --</option>
                    {allReviews.filter(r => Number(r.employee) !== Number(user?.id)).map(r => (
                      <option key={r.id} value={r.id}>
                        Review #{r.id} - {r.employee_name || `Employee ${r.employee}`} ({r.cycle_name || `Cycle ${r.cycle}`})
                      </option>
                    ))}
                  </select>
                )}
                <small className="text-muted d-block mt-1">
                  Total reviews in system: {allReviews.length} | 
                  Available for peer feedback: {allReviews.filter(r => Number(r.employee) !== Number(user?.id)).length}
                </small>
              </div>
              <div className="mb-2"><label className="form-label">Collaboration feedback</label><textarea className="form-control" value={peerForm.collaboration_feedback} onChange={e => setPeerForm(p => ({ ...p, collaboration_feedback: e.target.value }))} required /></div>
              <div className="mb-2"><label className="form-label">Strengths</label><textarea className="form-control" value={peerForm.strengths} onChange={e => setPeerForm(p => ({ ...p, strengths: e.target.value }))} /></div>
              <div className="mb-2"><label className="form-label">Areas for improvement</label><textarea className="form-control" value={peerForm.areas_for_improvement} onChange={e => setPeerForm(p => ({ ...p, areas_for_improvement: e.target.value }))} /></div>
              <div className="form-check mb-2"><input className="form-check-input" id="anon" type="checkbox" checked={peerForm.is_anonymous} onChange={e => setPeerForm(p => ({ ...p, is_anonymous: e.target.checked }))} /><label className="form-check-label" htmlFor="anon">Submit anonymously</label></div>
              <div className="small text-muted">Before submitting, the app checks the review's peer review deadline and prevents submissions after deadline. Also you cannot submit feedback for your own review.</div>
            </div>
            <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowPeerForm(false)}>Close</button><button type="submit" className="btn btn-primary">Submit</button></div>
          </form>
        </div>
      </div>

      {/* Manager Modal */}
      <div className={`modal ${showManagerForm ? "d-block" : ""}`} tabIndex={-1} style={{ background: showManagerForm ? "rgba(0,0,0,0.45)" : undefined }}>
        <div className="modal-dialog modal-lg">
          {managerMode === "view" ? (
            <div className="modal-content">
              <div className="modal-header"><h5 className="modal-title">View Manager Review</h5><button type="button" className="btn-close" onClick={() => setShowManagerForm(false)} /></div>
              <div className="modal-body">
                <div className="mb-2"><label className="form-label">Review ID</label><div className="form-control readonly">{managerForm.review}</div></div>
                <div className="mb-2"><label className="form-label">Performance summary</label><div className="form-control readonly" style={{whiteSpace:'pre-wrap'}}>{managerForm.performance_summary}</div></div>
                <div className="mb-2"><label className="form-label">Goals comment</label><div className="form-control readonly">{managerForm.goals_achievement_comment}</div></div>
                <div className="mb-2"><label className="form-label">Overall rating</label><div className="form-control readonly">{managerForm.overall_rating ?? '-'}</div></div>
              </div>
              <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowManagerForm(false)}>Close</button>{(isAdmin || isHR) && managerForm.id && <button type="button" className="btn btn-danger" onClick={() => deleteManager(managerForm.id)}>Delete</button>}</div>
            </div>
          ) : (
            <form className="modal-content" onSubmit={submitManager}>
              <div className="modal-header"><h5 className="modal-title">{managerMode === "edit" ? "Edit Manager Review" : "Create Manager Review"}</h5><button type="button" className="btn-close" onClick={() => setShowManagerForm(false)} /></div>
              <div className="modal-body">
                <div className="mb-2"><label className="form-label">Review ID</label><input className="form-control" value={managerForm.review} onChange={e => setManagerForm(p => ({ ...p, review: e.target.value }))} required /></div>
                <div className="mb-2"><label className="form-label">Performance summary</label><textarea className="form-control" value={managerForm.performance_summary} onChange={e => setManagerForm(p => ({ ...p, performance_summary: e.target.value }))} required /></div>
                <div className="mb-2"><label className="form-label">Strengths</label><textarea className="form-control" value={managerForm.strengths} onChange={e => setManagerForm(p => ({ ...p, strengths: e.target.value }))} /></div>
                <div className="mb-2"><label className="form-label">Areas for improvement</label><textarea className="form-control" value={managerForm.areas_for_improvement} onChange={e => setManagerForm(p => ({ ...p, areas_for_improvement: e.target.value }))} /></div>
                <div className="mb-2"><label className="form-label">Goals achievement comment</label><textarea className="form-control" value={managerForm.goals_achievement_comment} onChange={e => setManagerForm(p => ({ ...p, goals_achievement_comment: e.target.value }))} required /></div>
                <div className="mb-2"><label className="form-label">Goals for next period</label><textarea className="form-control" value={managerForm.goals_for_next_period} onChange={e => setManagerForm(p => ({ ...p, goals_for_next_period: e.target.value }))} required /></div>
                <div className="mb-2"><label className="form-label">Overall rating (optional)</label><input type="number" step="0.01" min="1" max="5" className="form-control" value={managerForm.overall_rating ?? ""} onChange={e => setManagerForm(p => ({ ...p, overall_rating: e.target.value === "" ? null : Number(e.target.value) }))} /></div>
              </div>
              <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => setShowManagerForm(false)}>Close</button><button type="submit" className="btn btn-primary">{managerMode === "edit" ? "Save" : "Create"}</button></div>
            </form>
          )}
        </div>
      </div>

      {/* Cycle Details Modal */}
      <div className={`modal ${showCycleDetails ? "d-block" : ""}`} tabIndex={-1} style={{ background: showCycleDetails ? "rgba(0,0,0,0.45)" : undefined }}>
        <div className="modal-dialog modal-md">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">Cycle Details</h5>
              <button type="button" className="btn-close" onClick={() => closeCycleDetails()} />
            </div>
            <div className="modal-body">
              {!cycleDetails && <div className="text-muted">No data</div>}
              {cycleDetails && (
                <div>
                  <div className="mb-2"><strong>{cycleDetails.name}</strong></div>
                  <div className="small text-muted mb-2">{cycleDetails.review_type} • {cycleDetails.status}</div>
                  <div className="mb-2 small text-muted">Start: {simpleDate(cycleDetails.start_date)} End: {simpleDate(cycleDetails.end_date)}</div>
                  {cycleDetails.description && <div className="mb-2">{cycleDetails.description}</div>}
                  <div className="mb-2"><strong>Participants:</strong> {cycleDetails.participant_count ?? cycleDetails.participants?.length ?? '-'}</div>
                </div>
              )}
            </div>
            <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => closeCycleDetails()}>Close</button></div>
          </div>
        </div>
      </div>

      {/* Stats Modal */}
      <div className={`modal ${showStatsModal ? "d-block" : ""}`} tabIndex={-1} style={{ background: showStatsModal ? "rgba(0,0,0,0.45)" : undefined }}>
        <div className="modal-dialog modal-md">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">Cycle Statistics</h5>
              <button type="button" className="btn-close" onClick={() => { setShowStatsModal(false); setStatsData(null); }} />
            </div>
            <div className="modal-body">
              {statsData ? (
                <>
                  <div className="mb-2"><strong>{statsData.cycle || statsData.name || statsData.cycle_name || "Cycle"}</strong></div>
                  <div className="mb-1 small text-muted">Participants: {statsData.total_participants ?? statsData.participant_count ?? "-"}</div>
                  <div className="mb-1 small text-muted">Total reviews: {statsData.total_reviews ?? statsData.review_count ?? "-"}</div>
                  <div className="mb-2"><strong>Reviews by status</strong></div>
                  {statsData.reviews_by_status ? (
                    <pre className="stats">{JSON.stringify(statsData.reviews_by_status, null, 2)}</pre>
                  ) : (
                    <div className="text-muted">No breakdown available.</div>
                  )}
                  {statsData.self_assessments_completed !== undefined && <div className="mt-2">Self assessments completed: {statsData.self_assessments_completed}</div>}
                  {statsData.manager_reviews_completed !== undefined && <div>Manager reviews completed: {statsData.manager_reviews_completed}</div>}
                  {statsData.peer_feedbacks_submitted !== undefined && <div>Peer feedbacks submitted: {statsData.peer_feedbacks_submitted}</div>}
                  {statsData.completion_rate !== undefined && <div>Completion rate: {statsData.completion_rate}</div>}
                </>
              ) : (
                <div className="text-muted">No statistics available.</div>
              )}
            </div>
            <div className="modal-footer"><button type="button" className="btn btn-secondary" onClick={() => { setShowStatsModal(false); setStatsData(null); }}>Close</button></div>
          </div>
        </div>
      </div>

    </div>
  );
}
