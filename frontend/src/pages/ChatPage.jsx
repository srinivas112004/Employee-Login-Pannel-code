// src/pages/ChatPage.jsx
import React, { useEffect, useState, useRef } from "react";
import { FaPaperPlane, FaTrash, FaEdit, FaCheckDouble } from "react-icons/fa";
import { format } from "date-fns";
import { useAuth } from "../context/AuthContext";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000";
const getHeaders = () => ({
  "Content-Type": "application/json",
  Authorization: `Bearer ${localStorage.getItem("access_token")}`,
});

export default function ChatPage({ BASE = API_BASE }) {
  const { user: profile } = useAuth();
  const [rooms, setRooms] = useState([]);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [messages, setMessages] = useState([]);
  const [msgText, setMsgText] = useState("");
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loadingRooms, setLoadingRooms] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [creatingRoom, setCreatingRoom] = useState(false);
  const [alertMsg, setAlertMsg] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [roomName, setRoomName] = useState("");
  const [roomType, setRoomType] = useState("group");
  const [allUsers, setAllUsers] = useState([]);
  const [selectedParticipants, setSelectedParticipants] = useState(new Set());
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [addMemberRoomId, setAddMemberRoomId] = useState(null);
  const [addMemberSelected, setAddMemberSelected] = useState(new Set());
  const [addingMembers, setAddingMembers] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [detailsRoom, setDetailsRoom] = useState(null);
  const [detailsParticipants, setDetailsParticipants] = useState([]);
  const messagesEndRef = useRef(null);

  // Day14: File upload state
  const [file, setFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [filesList, setFilesList] = useState([]);

  // Channels & broadcast
  const [channels, setChannels] = useState([]);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [channelMessage, setChannelMessage] = useState("");
  const [channelMessages, setChannelMessages] = useState([]);
  const [broadcasting, setBroadcasting] = useState(false);

  // WebSocket refs
  const channelWsRef = useRef(null);
  const reconnectRef = useRef(null);

  useEffect(() => {
    fetchRooms();
    fetchOnlineUsers();
    fetchNotifications();
    fetchUnreadCount();
    loadChannels();
    const last = localStorage.getItem("chat_last_room");
    if (last) setSelectedRoom(last);
    // eslint-disable-next-line
  }, []);

  useEffect(() => {
    if (selectedRoom) {
      localStorage.setItem("chat_last_room", selectedRoom);
      fetchRoomMessages(selectedRoom);
      loadRoomFiles(selectedRoom);
    } else {
      setMessages([]);
      setFilesList([]);
    }
  }, [selectedRoom]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (selectedChannel) {
      connectToChannelWS(selectedChannel);
      loadChannelMessages(selectedChannel);
    } else {
      closeChannelWS();
      setChannelMessages([]);
    }
    // eslint-disable-next-line
  }, [selectedChannel]);

  const showAlert = (text, type = "danger", autoClose = 5000) => {
    setAlertMsg({ text, type });
    if (autoClose) setTimeout(() => setAlertMsg(null), autoClose);
  };

  const parseList = async (res) => {
    try {
      const data = await res.json().catch(() => null);
      if (!data) return [];
      return Array.isArray(data) ? data : data.results ?? [];
    } catch {
      return [];
    }
  };

  const parseSingle = async (res) => {
    try {
      const data = await res.json().catch(() => null);
      return data;
    } catch {
      return null;
    }
  };

  const showServerError = async (res, fallback = "Request failed") => {
    let msg = `${fallback} (status ${res.status})`;
    try {
      const clone = res.clone();
      let body = null;
      try {
        body = await res.json();
      } catch (jsonErr) {
        try {
          body = await clone.text();
        } catch (tErr) {
          body = null;
        }
      }
      if (body) {
        if (typeof body === "string") {
          msg += `: ${body}`;
          console.error("Server error text:", body);
        } else {
          if (body.detail) msg += `: ${body.detail}`;
          else if (body.error) msg += `: ${body.error}`;
          else if (body.message) msg += `: ${body.message}`;
          else {
            const parts = [];
            for (const k of Object.keys(body)) {
              const v = body[k];
              if (Array.isArray(v)) parts.push(`${k}: ${v.join(", ")}`);
              else if (typeof v === "string") parts.push(`${k}: ${v}`);
              else parts.push(`${k}: ${JSON.stringify(v)}`);
            }
            if (parts.length) msg += `: ${parts.join(" | ")}`;
          }
          console.error("Server error body:", body);
        }
      } else {
        const text = await res.text().catch(() => null);
        if (text) {
          msg += `: ${text}`;
          console.error("Server error text:", text);
        }
      }
    } catch (err) {
      console.error("error parsing server error", err);
    }
    showAlert(msg, "danger", 15000);
    return msg;
  };

  function normalizeMessagesOrder(list = []) {
    if (!Array.isArray(list) || list.length === 0) return [];
    const getDate = (m) => new Date(m.created_at ?? m.timestamp ?? m.createdAt ?? 0).getTime() || 0;
    return list.slice().sort((a, b) => getDate(a) - getDate(b));
  }

  const refreshMessages = async (roomId = selectedRoom) => {
    if (!roomId) return;
    await fetchRoomMessages(roomId);
  };

  async function fetchRooms() {
    setLoadingRooms(true);
    try {
      const res = await fetch(`${BASE}/api/chat/rooms/`, { headers: getHeaders() });
      if (!res.ok) {
        await showServerError(res, "Failed to load rooms");
        setRooms([]);
        return;
      }
      const list = await parseList(res);
      setRooms(list);
      if (!selectedRoom && list.length > 0) {
        const id = list[0]._id ?? list[0].id ?? list[0].pk ?? null;
        if (id) setSelectedRoom(String(id));
      }
    } catch (err) {
      console.error(err);
      showAlert("Failed to load rooms", "danger");
      setRooms([]);
    } finally {
      setLoadingRooms(false);
    }
  }

  async function searchRooms(q) {
    if (!q || !q.trim()) {
      fetchRooms();
      return;
    }
    try {
      const res = await fetch(`${BASE}/api/chat/rooms/search/?q=${encodeURIComponent(q)}`, { headers: getHeaders() });
      if (!res.ok) {
        await showServerError(res, "Room search failed");
        return;
      }
      const list = await parseList(res);
      setRooms(list);
    } catch (err) {
      console.error(err);
      showAlert("Room search failed", "danger");
    }
  }

  async function deleteRoom(id) {
    if (!window.confirm("Delete room?")) return;
    try {
      const res = await fetch(`${BASE}/api/chat/rooms/${id}/`, { method: "DELETE", headers: getHeaders() });
      if (!res.ok) {
        await showServerError(res, "Delete room failed");
        return;
      }
      showAlert("Room deleted", "success");
      if (String(selectedRoom) === String(id)) setSelectedRoom(null);
      await fetchRooms();
    } catch (err) {
      console.error(err);
      showAlert("Delete failed", "danger");
    }
  }

  async function fetchRoomMessages(roomId) {
    if (!roomId) return;
    setLoadingMessages(true);
    try {
      const res = await fetch(`${BASE}/api/chat/rooms/${roomId}/messages/`, { headers: getHeaders() });
      if (!res.ok) {
        await showServerError(res, "Failed to load messages");
        setMessages([]);
        return;
      }
      const list = await parseList(res);
      setMessages(normalizeMessagesOrder(list));
    } catch (err) {
      console.error(err);
      showAlert("Failed to load messages", "danger");
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  }

  // sendMessage handles text and file upload (uses /api/chat/files/upload/)
  async function sendMessage() {
    if (!msgText || !msgText.trim()) {
      if (!file) return;
    }
    setSending(true);
    try {
      if (file) {
        setUploading(true);
        const token = localStorage.getItem("access_token");
        const formData = new FormData();
        formData.append("file", file);
        formData.append("room_id", selectedRoom);
        formData.append("content", msgText || "");
        const response = await fetch(`${BASE}/api/chat/files/upload/`, {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        });
        if (!response.ok) {
          await showServerError(response, "File upload failed");
        } else {
          const data = await response.json().catch(() => null);
          showAlert("File uploaded", "success");
          setFile(null);
          setFilePreview(null);
          await fetchRoomMessages(selectedRoom);
          await loadRoomFiles(selectedRoom);
        }
        setUploading(false);
      } else {
        const payload = { room: selectedRoom, content: msgText, message_type: "text" };
        const res = await fetch(`${BASE}/api/chat/messages/`, {
          method: "POST",
          headers: getHeaders(),
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          await showServerError(res, "Send failed");
          return;
        }
        setMsgText("");
        await fetchRoomMessages(selectedRoom);
        await fetchRooms();
        await fetchUnreadCount();
      }
    } catch (err) {
      console.error(err);
      showAlert("Send failed", "danger");
    } finally {
      setSending(false);
    }
  }

  async function editMessage(id, content) {
    try {
      const res = await fetch(`${BASE}/api/chat/messages/${id}/`, {
        method: "PATCH",
        headers: getHeaders(),
        body: JSON.stringify({ content }),
      });
      if (!res.ok) {
        if (res.status === 403) {
          try {
            const b = await res.json().catch(() => null);
            showAlert(b?.error ?? b?.detail ?? "Forbidden", "danger");
          } catch {
            showAlert("Forbidden", "danger");
          }
        } else {
          await showServerError(res, "Edit failed");
        }
        return;
      }
      showAlert("Message updated", "success");
      await fetchRoomMessages(selectedRoom);
    } catch (err) {
      console.error(err);
      showAlert("Edit failed", "danger");
    }
  }

  async function handleDeleteMessage(id) {
    try {
      await deleteMessage(id);
    } catch (err) {
      console.error("handleDeleteMessage error:", err);
      showAlert("Failed to delete message", "danger");
    }
  }

  async function deleteMessage(id) {
    if (!window.confirm("Delete message?")) return;
    try {
      const res = await fetch(`${BASE}/api/chat/messages/${id}/`, { method: "DELETE", headers: getHeaders() });
      if (!res.ok) {
        await showServerError(res, "Delete message failed");
        return;
      }
      showAlert("Message deleted", "success");
      await fetchRoomMessages(selectedRoom);
    } catch (err) {
      console.error(err);
      showAlert("Delete failed", "danger");
    }
  }

  // MARK READ: backend uses POST /api/chat/messages/{id}/mark-read/
  async function markMessageRead(id) {
    if (!id) {
      showAlert("Missing message id to mark read", "warning");
      return;
    }
    const cleaned = sanitizeRoomId(id);
    const url = `${BASE.replace(/\/$/, "")}/api/chat/messages/${cleaned}/mark-read/`;
    try {
      const res = await fetch(url, { method: "POST", headers: getHeaders() });
      console.log("[markMessageRead] POST", url, "=>", res.status);
      if (res.ok) {
        await fetchNotifications();
        await fetchUnreadCount();
        showAlert("Marked read", "success");
        return;
      } else {
        const body = await res.text().catch(() => null);
        console.warn("[markMessageRead] failed:", res.status, body);
        try {
          const maybeJson = JSON.parse(body || "{}");
          if (maybeJson?.detail || maybeJson?.error || maybeJson?.message) {
            showAlert(maybeJson.detail ?? maybeJson.error ?? maybeJson.message, "danger", 8000);
            return;
          }
        } catch {}
        await showServerError(res, "Mark read failed");
      }
    } catch (err) {
      console.error("[markMessageRead] error:", err);
      showAlert("Mark read failed (network error)", "danger");
    }
  }

  async function fetchOnlineUsers() {
    try {
      const res = await fetch(`${BASE}/api/chat/online-status/online-users/`, { headers: getHeaders() });
      if (!res.ok) {
        console.warn("fetchOnlineUsers failed", res.status);
        setOnlineUsers([]);
        return;
      }
      const list = await parseList(res);
      setOnlineUsers(list);
    } catch (err) {
      console.error(err);
      setOnlineUsers([]);
    }
  }

  async function fetchNotifications() {
    try {
      const res = await fetch(`${BASE}/api/chat/notifications/`, { headers: getHeaders() });
      if (!res.ok) {
        console.warn("fetchNotifications failed", res.status);
        setNotifications([]);
        return;
      }
      const list = await parseList(res);
      setNotifications(list);
    } catch (err) {
      console.error(err);
      setNotifications([]);
    }
  }

  async function fetchUnreadCount() {
    try {
      const res = await fetch(`${BASE}/api/chat/notifications/unread-count/`, { headers: getHeaders() });
      if (!res.ok) return;
      const data = await res.json().catch(() => null);
      setUnreadCount(data?.count ?? 0);
    } catch (err) {
      console.error(err);
    }
  }

  async function markAllNotificationsRead() {
    try {
      const res = await fetch(`${BASE}/api/chat/notifications/mark-all-read/`, { method: "POST", headers: getHeaders() });
      if (!res.ok) {
        await showServerError(res, "Mark all read failed");
        return;
      }
      await fetchNotifications();
      await fetchUnreadCount();
      showAlert("All notifications marked read", "success");
    } catch (err) {
      console.error(err);
      showAlert("Mark all failed", "danger");
    }
  }

  async function markNotificationRead(notificationId, notificationObj = null) {
    if (!notificationId) return;
    const msgIdFromNotif = notificationObj?.message_id ?? notificationObj?.data?.message_id ?? notificationObj?.meta?.message_id ?? null;
    const base = BASE.replace(/\/$/, "");
    const attempts = [
      { url: `${base}/api/chat/notifications/${sanitizeRoomId(notificationId)}/mark-read/`, body: null },
      { url: `${base}/api/chat/notifications/mark-read/`, body: { id: notificationId } },
      { url: `${base}/api/chat/notifications/mark-read/`, body: { notification_id: notificationId } },
      { url: `${base}/api/chat/notifications/mark-read/`, body: { ids: [notificationId] } },
    ];
    for (const attempt of attempts) {
      try {
        const opts = { method: "POST", headers: getHeaders() };
        if (attempt.body !== null) opts.body = JSON.stringify(attempt.body);
        const res = await fetch(attempt.url, opts);
        console.log("[markNotificationRead] try:", attempt.url, attempt.body, "=>", res.status);
        if (res.ok) {
          await fetchNotifications();
          await fetchUnreadCount();
          showAlert("Notification marked read", "success");
          return;
        } else {
          const text = await res.text().catch(() => null);
          console.warn("[markNotificationRead] failed body:", attempt.url, res.status, text);
        }
      } catch (err) {
        console.error("[markNotificationRead] error trying", attempt.url, err);
      }
    }
    if (msgIdFromNotif) {
      await markMessageRead(msgIdFromNotif);
      return;
    }
    showAlert("Could not mark notification read (endpoint not found). See console for details.", "warning", 10000);
  }

  function getCurrentUserId() {
    if (!profile) return null;
    return profile.id ?? profile._id ?? profile.pk ?? profile.user_id ?? null;
  }

  async function loadAllUsers() {
    setLoadingUsers(true);
    try {
      const candidates = [
        "/api/auth/users/",
        "/api/users/",
        "/api/accounts/users/",
        "/api/dashboard/users/",
        "/api/v1/users/",
        "/api/chat/users/",
      ].map((p) => (p.startsWith("http") ? p : `${BASE}${p}`));

      for (const url of candidates) {
        try {
          const res = await fetch(url, { headers: getHeaders() });
          if (!res.ok) continue;
          const data = await res.json().catch(() => null);
          const arr = Array.isArray(data) ? data : data?.results ?? [];
          if (Array.isArray(arr) && arr.length > 0) {
            const normalized = arr
              .map((u) => ({
                id: u.id ?? u._id ?? u.pk ?? u.user_id ?? null,
                name:
                  u.full_name ||
                  u.name ||
                  u.username ||
                  (u.first_name && `${u.first_name} ${u.last_name}`) ||
                  u.email ||
                  String(u.id ?? u._id ?? u.pk ?? ""),
              }))
              .filter((x) => x.id != null);
            setAllUsers(normalized);
            setLoadingUsers(false);
            return;
          }
        } catch (err) {}
      }
      setAllUsers([]);
    } catch (err) {
      console.error(err);
      setAllUsers([]);
    } finally {
      setLoadingUsers(false);
    }
  }

  function openCreateModal() {
    const me = getCurrentUserId();
    const initial = new Set();
    if (me != null) initial.add(me);
    setSelectedParticipants(initial);
    setRoomName("");
    setRoomType("group");
    setShowCreateModal(true);
    if (!allUsers || allUsers.length === 0) loadAllUsers();
  }

  function toggleParticipant(id) {
    setSelectedParticipants((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  }

  async function submitCreateRoomHandler(e) {
    e.preventDefault();
    const name = (roomName || "").trim();
    const type = (roomType || "group").trim() || "group";
    const allowed = ["direct", "group", "department", "broadcast"];
    const normalizedType = allowed.includes(type) ? type : "group";
    if (!name) {
      showAlert("Room name is required", "danger");
      return;
    }
    setCreatingRoom(true);
    try {
      const me = getCurrentUserId();
      const participantsSet = new Set(Array.from(selectedParticipants));
      if (me != null) participantsSet.add(me);
      const participants = Array.from(participantsSet).map((id) => {
        if (/^\d+$/.test(String(id))) return Number(id);
        return id;
      });
      const payload = { name, room_type: normalizedType, type: normalizedType };
      if (participants.length > 0) payload.participants = participants;
      const res = await fetch(`${BASE}/api/chat/rooms/`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        await showServerError(res, "Create room failed");
        return;
      }
      const created = await parseSingle(res);
      showAlert("Room created", "success");
      setShowCreateModal(false);
      await fetchRooms();
      const id = created?._id ?? created?.id ?? created?.room_id ?? created?.pk ?? null;
      if (id) setSelectedRoom(String(id));
    } catch (err) {
      console.error(err);
      showAlert("Create room failed", "danger");
    } finally {
      setCreatingRoom(false);
    }
  }

  function extractParticipantIds(room) {
    const participantsRaw = room?.participants ?? room?.participants_ids ?? room?.participant_ids ?? [];
    const normalized = new Set();
    if (Array.isArray(participantsRaw)) {
      for (const p of participantsRaw) {
        if (typeof p === "object") {
          const pid = p.id ?? p._id ?? p.pk ?? p.user_id ?? null;
          if (pid != null) normalized.add(pid);
        } else {
          normalized.add(p);
        }
      }
    }
    return normalized;
  }

  function sanitizeRoomId(raw) {
    if (!raw) return raw;
    const s = String(raw);
    const m = s.match(/[a-fA-F0-9\-]{6,}|[0-9]{3,}/);
    if (m) return m[0];
    return s.replace(/[^a-zA-Z0-9\-_]/g, "");
  }

  function openAddMemberModal(room) {
    if (!room) return;
    const id = room._id ?? room.id ?? room.pk ?? room.room_id ?? null;
    setAddMemberRoomId(String(id));
    const existing = extractParticipantIds(room);
    setAddMemberSelected(existing);
    setShowAddMemberModal(true);
    if (!allUsers || allUsers.length === 0) loadAllUsers();
  }

  function toggleAddMember(id) {
    setAddMemberSelected((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  }

  async function tryPatchWithCandidates(url, payloadCandidates) {
    for (const candidate of payloadCandidates) {
      try {
        const res = await fetch(url, { method: "PATCH", headers: getHeaders(), body: JSON.stringify(candidate) });
        console.log("[PATCH TRY]", url, candidate, "=>", res.status);
        if (res.ok) {
          return { ok: true, res };
        } else {
          const txt = await res.text().catch(() => null);
          console.warn("[PATCH FAIL BODY]", url, candidate, res.status, txt);
        }
      } catch (err) {
        console.error("[PATCH ERROR]", url, candidate, err);
      }
    }
    return { ok: false };
  }

  async function submitAddMembersHandler(e) {
    e.preventDefault();
    if (!addMemberRoomId) {
      showAlert("Missing room id", "danger");
      return;
    }
    setAddingMembers(true);
    try {
      const participants = Array.from(addMemberSelected).map((id) => {
        if (/^\d+$/.test(String(id))) return Number(id);
        return id;
      });
      const clean = sanitizeRoomId(addMemberRoomId);
      const url = `${BASE.replace(/\/$/, "")}/api/chat/rooms/${clean}/`;
      const candidates = [
        { participants },
        { participants_ids: participants },
        { participant_ids: participants },
        { participants: participants.map((p) => (typeof p === "number" ? p : p)) },
      ];
      console.log("[ADD MEMBERS] URL:", url, "payload candidates:", candidates);
      const result = await tryPatchWithCandidates(url, candidates);
      if (!result.ok) {
        showAlert(`Add members failed (server returned error). Check console for full response.`, "danger", 12000);
        try {
          const resAttempt = await fetch(url, { method: "PATCH", headers: getHeaders(), body: JSON.stringify({ participants }) });
          if (!resAttempt.ok) {
            const body = await resAttempt.text().catch(() => null);
            console.error("[FINAL ATTEMPT BODY]", resAttempt.status, body);
            await showServerError(resAttempt, "Add members failed");
          }
        } catch (err) {
          console.error("Final attempt error", err);
        }
        return;
      }
      showAlert("Participants updated", "success");
      setShowAddMemberModal(false);
      setAddMemberRoomId(null);
      await fetchRooms();
      if (String(selectedRoom) === String(addMemberRoomId)) {
        await fetchRoomMessages(selectedRoom);
      }
    } catch (err) {
      console.error(err);
      showAlert("Add members failed", "danger");
    } finally {
      setAddingMembers(false);
    }
  }

  function getParticipantDisplayNameFromObj(obj) {
    if (!obj) return "User";
    return (
      obj.full_name ||
      obj.name ||
      obj.username ||
      (obj.first_name && `${obj.first_name} ${obj.last_name}`) ||
      (obj.email ? String(obj.email).split("@")[0] : null) ||
      String(obj.id ?? obj._id ?? obj.pk ?? "")
    );
  }

  function openDetailsModal(room) {
    if (!room) return;
    setDetailsRoom(room);
    const participantsRaw = room.participants ?? room.participants_ids ?? room.participant_ids ?? [];
    const list = [];
    if (Array.isArray(participantsRaw)) {
      for (const p of participantsRaw) {
        if (typeof p === "object") {
          const pid = p.id ?? p._id ?? p.pk ?? p.user_id ?? null;
          const name = getParticipantDisplayNameFromObj(p);
          list.push({ id: pid ?? name, name });
        } else {
          const found = allUsers.find((u) => String(u.id) === String(p));
          if (found) {
            list.push({ id: found.id, name: found.name });
          } else {
            list.push({ id: p, name: String(p) });
          }
        }
      }
    }
    setDetailsParticipants(list);
    setShowDetailsModal(true);
    if (!allUsers || allUsers.length === 0) loadAllUsers();
  }

  function scrollToBottom() {
    if (messagesEndRef.current) messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
  }

  function shortSender(m) {
    if (!m) return "User";
    const senderObj = m.sender ?? m.user ?? null;
    const username =
      m.sender_username ||
      m.sender_name ||
      m.sender_email ||
      (senderObj && (senderObj.full_name || senderObj.name || senderObj.username || senderObj.email)) ||
      m.sender ||
      m.senderId ||
      "";
    if (!username) return "User";
    const s = String(username);
    if (s.includes("@")) return s.split("@")[0];
    const tokens = s.split(/\s+/);
    return tokens.slice(0, 3).join(" ");
  }

  function isOwnerOfMessage(m) {
    if (!profile) return false;
    const userIds = [profile.id, profile._id, profile.user_id, profile.pk].filter(Boolean).map(String);
    const userEmails = [profile.email, profile.user_email].filter(Boolean).map(String);
    const userUsernames = [profile.username, profile.user_name].filter(Boolean).map(String);
    const senderId = m.sender_id ?? m.sender?._id ?? m.sender?.id ?? m.senderId ?? null;
    const senderIdStr = senderId != null ? String(senderId) : null;
    if (senderIdStr && userIds.includes(senderIdStr)) return true;
    const senderString = m.sender_username ?? m.sender?.username ?? m.sender?.email ?? m.sender ?? m.sender_name ?? m.sender_email ?? null;
    if (senderString) {
      const s = String(senderString);
      if (userEmails.includes(s) || userUsernames.includes(s) || userIds.includes(s)) return true;
      const at = s.match(/^([^@]+)@/);
      if (at && profile.email && at[1] === profile.email.split("@")[0]) return true;
    }
    if (m.is_owner === true || m.is_owner === "true") return true;
    return false;
  }

  function displayNameForUser(u) {
    if (!u) return "User";
    const userObj = u.user || u;
    const firstName = userObj.first_name || userObj.firstName || "";
    const lastName = userObj.last_name || userObj.lastName || "";
    const fullName = `${firstName} ${lastName}`.trim();
    return fullName || userObj.full_name || userObj.name || userObj.username || (userObj.email ? String(userObj.email).split("@")[0] : "User");
  }

  // --- helper: get selected room object & display name ---
  function getSelectedRoomObj() {
    if (!selectedRoom || !rooms) return null;
    return (
      rooms.find(
        (r) =>
          String(r._id ?? r.id ?? r.pk ?? r.room_id ?? r.roomId ?? r.id_str ?? "") === String(selectedRoom)
      ) ?? null
    );
  }

  function getSelectedRoomName() {
    const r = getSelectedRoomObj();
    if (!r) return `Room ${selectedRoom || ""}`;
    return (
      r.title ??
      r.name ??
      r.display_name ??
      r.room_name ??
      r.label ??
      (r.created_by_details && (r.created_by_details.first_name || r.created_by_details.email)) ??
      `Room ${r._id ?? r.id ?? selectedRoom}`
    );
  }

  // Day14: load room files
  async function loadRoomFiles(roomId, fileType = null, limit = 50, offset = 0) {
    if (!roomId) return;
    try {
      let url = `${BASE}/api/chat/files/room-files/?room_id=${roomId}&limit=${limit}&offset=${offset}`;
      if (fileType) url += `&file_type=${fileType}`;
      const res = await fetch(url, { method: "GET", headers: getHeaders() });
      if (!res.ok) {
        console.warn("loadRoomFiles failed", res.status);
        setFilesList([]);
        return;
      }
      const data = await res.json().catch(() => null);
      setFilesList(data?.files ?? data?.results ?? data ?? []);
    } catch (err) {
      console.error("loadRoomFiles error", err);
      setFilesList([]);
    }
  }

  function handleFileChange(e) {
    const selected = e.target.files[0];
    if (!selected) return;
    setFile(selected);
    if (selected.type && selected.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onloadend = () => setFilePreview(reader.result);
      reader.readAsDataURL(selected);
    } else {
      setFilePreview(null);
    }
  }

  // Channels: load, create, broadcast, messages
  async function loadChannels() {
    try {
      const res = await fetch(`${BASE}/api/chat/channels/`, { headers: getHeaders() });
      if (!res.ok) {
        const text = await res.text().catch(() => null);
        console.warn("loadChannels failed", res.status, text);
        setChannels([]);
        return;
      }
      const raw = await res.json().catch(() => null);
      const list = Array.isArray(raw) ? raw : raw?.results ?? raw?.channels ?? [];
      setChannels(list);
      if (list.length > 0 && !selectedChannel) {
        const first = list[0];
        const id = first.id ?? first._id ?? first.pk ?? first.channel_id ?? null;
        if (id) {
          setSelectedChannel(String(id));
          loadChannelMessages(id);
        }
      }
    } catch (err) {
      console.error("loadChannels error", err);
      setChannels([]);
    }
  }

  async function createChannel(channelData) {
    try {
      const res = await fetch(`${BASE}/api/chat/channels/`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(channelData),
      });
      if (!res.ok) {
        await showServerError(res, "Create channel failed");
        return null;
      }
      const data = await res.json().catch(() => null);
      await loadChannels();
      return data;
    } catch (err) {
      console.error("createChannel error", err);
      return null;
    }
  }

  async function loadChannelMessages(channelId) {
    if (!channelId) return;
    try {
      const res = await fetch(`${BASE}/api/chat/channels/${channelId}/messages/`, { headers: getHeaders() });
      if (!res.ok) {
        console.warn("loadChannelMessages failed", res.status);
        setChannelMessages([]);
        return;
      }
      const json = await res.json().catch(() => null);
      setChannelMessages(json?.messages ?? json?.results ?? json ?? []);
    } catch (err) {
      console.error("loadChannelMessages error", err);
      setChannelMessages([]);
    }
  }

  async function sendBroadcast(channelId, content) {
    if (!channelId || !content?.trim()) {
      showAlert("Select channel and enter message to broadcast", "warning");
      return;
    }
    setBroadcasting(true);
    try {
      const res = await fetch(`${BASE}/api/chat/channels/${channelId}/broadcast/`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ content, message_type: "text" }),
      });
      if (!res.ok) {
        await showServerError(res, "Broadcast failed");
        return;
      }
      showAlert("Broadcast sent", "success");
      setChannelMessage("");
      await loadChannelMessages(channelId);
      await loadChannels();
    } catch (err) {
      console.error("sendBroadcast error", err);
      showAlert("Broadcast failed", "danger");
    } finally {
      setBroadcasting(false);
    }
  }

  // WebSocket helpers for channels
  function closeChannelWS() {
    try {
      if (reconnectRef.current) { clearTimeout(reconnectRef.current); reconnectRef.current = null; }
      if (channelWsRef.current) {
        channelWsRef.current.onopen = null;
        channelWsRef.current.onmessage = null;
        channelWsRef.current.onerror = null;
        channelWsRef.current.onclose = null;
        try { channelWsRef.current.close(); } catch {}
        channelWsRef.current = null;
      }
    } catch (e) {
      console.warn("closeChannelWS error", e);
    }
  }

  function connectToChannelWS(channelId) {
    closeChannelWS();
    const token = localStorage.getItem("access_token");
    if (!token || !channelId) return;
    const baseNoSlash = BASE.replace(/\/$/, "");
    // build ws base: replace http(s) with ws(s)
    let wsBase;
    if (baseNoSlash.startsWith("https://")) wsBase = baseNoSlash.replace(/^https:\/\//i, "wss://");
    else if (baseNoSlash.startsWith("http://")) wsBase = baseNoSlash.replace(/^http:\/\//i, "ws://");
    else wsBase = `${window.location.origin.replace(/^http/, "ws")}`;

    const wsUrl = `${wsBase}/ws/channel/${channelId}/?token=${encodeURIComponent(token)}`;

    try {
      const ws = new WebSocket(wsUrl);
      channelWsRef.current = ws;
      ws.onopen = () => { console.log("Connected channel WS:", channelId); };
      ws.onmessage = (evt) => {
        try {
          const data = JSON.parse(evt.data);
          if (data.type === "broadcast") {
            const broadcast = data.data;
            setChannelMessages((prev) => [broadcast, ...prev]);
            const senderName = data.sender_name ?? (broadcast?.sender?.first_name ?? "Someone");
            const snippet = String(broadcast?.content ?? "").slice(0, 120);
            if ("Notification" in window && Notification.permission === "granted") {
              try { new Notification("New Broadcast", { body: `${senderName}: ${snippet}` }); } catch (e) {}
            }
          } else if (data.type === "channel_update") {
            loadChannels();
          }
        } catch (err) {
          console.error("WS parse error", err);
        }
      };
      ws.onerror = (err) => console.error("channel ws error", err);
      ws.onclose = (ev) => {
        console.log("channel ws closed, reconnect in 3s", ev.code, ev.reason);
        channelWsRef.current = null;
        reconnectRef.current = setTimeout(() => {
          if (selectedChannel && String(selectedChannel) === String(channelId)) connectToChannelWS(channelId);
        }, 3000);
      };
    } catch (err) {
      console.error("connectToChannelWS error", err);
    }
  }

  function reactToMessageLocal(messageId, reaction) {
    showAlert(`Reacted ${reaction}`, "success");
  }

  // Render
  return (
    <div className="min-h-100 d-flex" style={{ fontFamily: "Inter, system-ui, -apple-system" }}>
      <div style={{ position: "fixed", top: 12, right: 12, zIndex: 1200 }}>
        {alertMsg && (
          <div className={`alert alert-${alertMsg.type} alert-dismissible fade show`} role="alert" style={{ minWidth: 320 }}>
            {alertMsg.text}
            <button type="button" className="btn-close" aria-label="Close" onClick={() => setAlertMsg(null)}></button>
          </div>
        )}
      </div>

      {/* Left: Rooms */}
      <aside style={{ width: 340, borderRight: "1px solid #e9ecef", padding: 14, background: "#fff" }}>
        <div className="d-flex align-items-center justify-content-between mb-3">
          <h5 className="mb-0">Rooms</h5>
          <div>
            <button className="btn btn-sm btn-outline-secondary me-1" onClick={() => fetchRooms()}>
              {loadingRooms ? "..." : "Refresh"}
            </button>
            <button className="btn btn-sm btn-primary" onClick={openCreateModal} disabled={creatingRoom}>
              New
            </button>
          </div>
        </div>

        <div className="mb-3 d-flex">
          <input className="form-control form-control-sm" placeholder="Search rooms..." onKeyDown={(e) => { if (e.key === "Enter") searchRooms(e.target.value); }} />
          <button className="btn btn-sm btn-light ms-2" onClick={() => { const q = document.querySelector('input[placeholder="Search rooms..."]')?.value ?? ""; searchRooms(q); }} > Search </button>
        </div>

        <div style={{ maxHeight: 360, overflow: "auto" }}>
          {loadingRooms ? ( <div className="text-muted">Loading rooms...</div> ) : rooms.length === 0 ? ( <div className="text-muted">No rooms found</div> ) : ( rooms.map((r) => {
            const id = String(r._id ?? r.id ?? r.pk ?? r.room_id ?? Math.random());
            const unreadBadge = r.unread_count ?? r.unread ?? 0;
            return (
              <div key={id} className={`p-2 mb-2 ${String(selectedRoom) === id ? "border rounded bg-light" : "border-bottom"}`} style={{ cursor: "pointer" }} onClick={() => setSelectedRoom(id)} >
                <div className="d-flex justify-content-between align-items-start">
                  <div>
                    <strong>{r.title ?? r.name ?? `Room {id}`}</strong>
                    <div className="small text-muted">{r.last_message_preview ?? r.description ?? ""}</div>
                  </div>
                  <div className="text-end">
                    {unreadBadge > 0 && <span className="badge bg-danger">{unreadBadge}</span>}
                    <div className="small text-muted">{r.participants ? r.participants.length : ""}</div>
                  </div>
                </div>
                <div className="mt-1 d-flex gap-2">
                  <button className="btn btn-sm btn-link p-0 me-2" onClick={(e) => { e.stopPropagation(); deleteRoom(id); }}> Delete </button>
                  <button className="btn btn-sm btn-link p-0 me-2" onClick={(e) => { e.stopPropagation(); openDetailsModal(r); }} > Details </button>
                  <button className="btn btn-sm btn-link p-0" onClick={(e) => { e.stopPropagation(); openAddMemberModal(r); }} > Add member </button>
                </div>
              </div>
            );
          }) )}
        </div>

        <hr />
        <div className="d-flex justify-content-between align-items-center mb-1">
          <h6 className="mb-0">Online</h6>
          <small className="text-muted">{onlineUsers.length}</small>
        </div>

        <ul className="list-unstyled small mb-3" style={{ maxHeight: 120, overflow: "auto" }}>
          {onlineUsers.map((u) => {
            const id = String(u._id ?? u.id ?? u.pk ?? Math.random());
            const display = displayNameForUser(u);
            return (
              <li key={id} className="d-flex align-items-center gap-2 mb-1">
                <span className="badge bg-success rounded-circle" style={{ width: "8px", height: "8px", padding: 0 }} title="Online" />
                <span>{display}</span>
              </li>
            );
          })}
        </ul>

        <div className="d-flex justify-content-between align-items-center">
          <h6 className="mb-0">Notifications</h6>
          <small className="text-muted">{unreadCount}</small>
        </div>

        <div style={{ maxHeight: 160, overflow: "auto" }}>
          {notifications.map((n) => {
            const id = String(n._id ?? n.id ?? Math.random());
            return (
              <div key={id} className="p-2 border-bottom">
                <div>{n.message ?? n.title ?? n.body}</div>
                <div className="small text-muted">{n.created_at ?? n.timestamp}</div>
                <div>
                  <button className="btn btn-sm btn-link p-0" onClick={() => markNotificationRead(id, n)} title="Mark read" aria-label="Mark notification read" > ✅ </button>
                </div>
              </div>
            );
          })}
          <div className="mt-2">
            <button className="btn btn-sm btn-outline-secondary" onClick={() => markAllNotificationsRead()}> Mark all read </button>
          </div>
        </div>
      </aside>

      {/* Main chat area */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", background: "#f8fafc" }}>
        {selectedRoom ? (
          <>
            <header style={{ padding: 12, borderBottom: "1px solid #e9ecef", background: "#fff" }} className="d-flex justify-content-between align-items-center">
              <div>
                <h5 className="mb-0">{getSelectedRoomName()}</h5>
                <small className="text-muted">Room ID: {selectedRoom}</small>
              </div>
              <div className="d-flex gap-2">
                <button className="btn btn-sm btn-outline-secondary" onClick={() => fetchRoomMessages(selectedRoom)} disabled={loadingMessages}> Refresh </button>
                <button className="btn btn-sm btn-outline-secondary" onClick={() => markAllNotificationsRead()}> Mark all read </button>
              </div>
            </header>

            <div style={{ padding: 16, flex: 1, overflow: "auto" }}>
              {loadingMessages ? (
                <div className="text-muted">Loading messages...</div>
              ) : messages.length === 0 ? (
                <div className="text-muted">No messages yet — start the conversation!</div>
              ) : (
                messages.map((m) => {
                  const id = String(m._id ?? m.id ?? m.pk ?? Math.random());
                  const owner = isOwnerOfMessage(m);
                  return (
                    <div key={id} className="mb-3 p-3" style={{ borderRadius: 8, background: "#fff", boxShadow: "0 1px 2px rgba(0,0,0,0.03)" }}>
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <strong>{shortSender(m)}</strong>
                          <div className="small text-muted">{m.created_at ? format(new Date(m.created_at), "PPP p") : ""}</div>
                        </div>
                        <div>
                          {owner && (
                            <>
                              <button className="btn btn-sm btn-link p-0 me-2" title="Edit message" aria-label="Edit message" onClick={() => { const c = prompt("Edit message:", m.content); if (c != null) editMessage(id, c); }} > <FaEdit /> </button>
                              <button className="btn btn-sm btn-link p-0 me-2" title="Delete message" aria-label="Delete message" onClick={() => handleDeleteMessage(id)}> <FaTrash /> </button>
                              <button className="btn btn-sm btn-link p-0" title="Mark message read" aria-label="Mark message read" onClick={() => markMessageRead(id)}> <FaCheckDouble /> </button>
                            </>
                          )}
                        </div>
                      </div>

                      <div className="mt-2">
                        {m.message_type === "file" || m.file_metadata ? (
                          <>
                            <div style={{ marginBottom: 8 }}>
                              <strong>{m.file_metadata?.file_name ?? "File"}</strong>
                              <div className="small text-muted">{m.content}</div>
                            </div>
                            <div>
                              <a href={`${BASE.replace(/\/$/, "")}${m.file_metadata?.file_url ?? m.file_url ?? ""}`} target="_blank" rel="noreferrer" className="btn btn-sm btn-outline-primary me-2">Open</a>
                              <a href={`${BASE.replace(/\/$/, "")}${m.file_metadata?.file_url ?? m.file_url ?? ""}`} download className="btn btn-sm btn-outline-secondary">Download</a>
                            </div>
                          </>
                        ) : (
                          <div>{m.content}</div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Footer with file upload */}
            <footer style={{ padding: 12, borderTop: "1px solid #e9ecef", background: "#fff" }} className="d-flex gap-2 align-items-center">
              <div style={{ display: "flex", gap: 8, alignItems: "center", width: "100%" }}>
                <input className="form-control" value={msgText} onChange={(e) => setMsgText(e.target.value)} placeholder="Type a message and press Enter (or attach a file)" onKeyDown={(e) => { if (e.key === "Enter") sendMessage(); }} disabled={sending} />
                <label className="btn btn-sm btn-outline-secondary mb-0" style={{ display: "inline-flex", alignItems: "center", gap: 8 }}>
                  <i className="bi bi-upload"></i> 
                  <input type="file" style={{ display: "none" }} onChange={handleFileChange} />
                </label>
                <button className="btn btn-primary" onClick={sendMessage} disabled={sending || (!msgText.trim() && !file)}>
                  {sending ? "Sending..." : <FaPaperPlane />}
                </button>
              </div>
            </footer>

            {/* Files gallery preview below messages */}
            <div style={{ padding: "8px 16px 16px", borderTop: "1px solid #f0f0f0", background: "#fafafa" }}>
              <h6 className="mb-2">Files in this room</h6>
              <div style={{ display: "flex", gap: 12, overflowX: "auto", paddingBottom: 8 }}>
                {filesList.length === 0 ? <div className="text-muted">No files</div> : filesList.map((f) => {
                  const fid = f._id ?? f.id ?? Math.random();
                  const meta = f.file_metadata ?? f;
                  const url = `${BASE.replace(/\/$/, "")}${meta.file_url ?? meta.url ?? ""}`;
                  const name = meta.file_name ?? meta.fileName ?? "file";
                  return (
                    <div key={fid} className="p-2 border rounded" style={{ minWidth: 160 }}>
                      <div className="small text-muted">{new Date(f.created_at ?? f.createdAt ?? Date.now()).toLocaleString()}</div>
                      <div style={{ fontWeight: 600 }}>{name}</div>
                      <div className="mt-1">
                        <a href={url} target="_blank" rel="noreferrer" className="btn btn-sm btn-outline-primary me-1">Open</a>
                        <a href={url} download className="btn btn-sm btn-outline-secondary">Download</a>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        ) : (
          <div style={{ padding: 24 }}>
            <h5>Select a room to start chatting</h5>
            <p className="text-muted">Or create a new room using the New button on the left.</p>
          </div>
        )}
      </main>

      {/* Right: Channels & Broadcast */}
      <aside style={{ width: 360, borderLeft: "1px solid #e9ecef", padding: 14, background: "#fff" }}>
        <div className="d-flex justify-content-between align-items-center mb-2">
          <h6 className="mb-0">Channels</h6>
          <div>
            <button className="btn btn-sm btn-outline-secondary me-1" onClick={() => loadChannels()}>Refresh</button>
            <button className="btn btn-sm btn-outline-primary" onClick={() => {
              const name = prompt("Channel name:");
              if (!name) return;
              createChannel({
                name,
                channel_type: "department",
                description: "",
                is_public: true,
                member_emails: [],
                settings: { allow_member_posts: true, allow_reactions: true, allow_replies: true }
              });
            }}>New</button>
          </div>
        </div>

        <div style={{ maxHeight: 180, overflow: "auto", marginBottom: 12 }}>
          {channels.length === 0 ? <div className="text-muted">No channels</div> : channels.map((ch) => {
            const cid = ch.id ?? ch._id ?? ch.pk ?? ch.channel_id;
            return (
              <div key={cid} className="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                <div>
                  <strong>{ch.name ?? ch.title ?? "Channel"}</strong>
                  <div className="small text-muted">{ch.channel_type}</div>
                </div>
                <div className="d-flex flex-column align-items-end">
                  {ch.is_public && <span className="badge bg-success mb-1">Public</span>}
                  <button className="btn btn-sm btn-outline-primary" onClick={async () => { setSelectedChannel(cid); await loadChannelMessages(cid); }}>Open</button>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mb-3">
          <h6>Broadcast</h6>
          <small className="text-muted">Select a channel and send announcement</small>
          <div className="mt-2">
            <select className="form-select form-select-sm mb-2" value={selectedChannel ?? ""} onChange={(e) => setSelectedChannel(e.target.value)}>
              <option value="">Select channel...</option>
              {channels.map((c) => {
                const cid = c.id ?? c._id ?? c.pk ?? c.channel_id;
                return <option key={cid} value={cid}>{c.name}</option>;
              })}
            </select>
            <textarea className="form-control form-control-sm mb-2" rows={3} placeholder="Announcement..." value={channelMessage} onChange={(e) => setChannelMessage(e.target.value)} />
            <div className="text-end">
              <button className="btn btn-sm btn-warning" onClick={() => sendBroadcast(selectedChannel, channelMessage)} disabled={!selectedChannel || !channelMessage.trim() || broadcasting}>{broadcasting ? "Sending..." : "Send Broadcast"}</button>
            </div>
          </div>
        </div>

        {selectedChannel && (
          <div>
            <h6 className="mb-2">Channel Broadcasts</h6>
            <div style={{ maxHeight: 220, overflow: "auto", border: "1px solid #eee", padding: 8, borderRadius: 6 }}>
              {channelMessages.length === 0 ? <div className="text-muted">No broadcasts</div> : channelMessages.map((m) => {
                const mid = String(m._id ?? m.id ?? m.pk ?? Math.random());
                return (
                  <div key={mid} className="mb-2 p-2 border rounded">
                    <div className="small text-muted">{m.sender?.first_name ?? "User"} • {m.created_at ? new Date(m.created_at).toLocaleString() : ""}</div>
                    <div>{m.content}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </aside>

      {/* Modals kept same as your original */}
      {showCreateModal && (
        <div className="modal show d-block" tabIndex="-1" role="dialog" style={{ background: "rgba(0,0,0,0.4)" }}>
          <div className="modal-dialog modal-lg" role="document">
            <form className="modal-content" onSubmit={submitCreateRoomHandler}>
              <div className="modal-header">
                <h5 className="modal-title">Create Room</h5>
                <button type="button" className="btn-close" aria-label="Close" onClick={() => setShowCreateModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-3">
                  <label className="form-label">Room name</label>
                  <input className="form-control" value={roomName} onChange={(e) => setRoomName(e.target.value)} required />
                </div>
                <div className="mb-3">
                  <label className="form-label">Room type</label>
                  <select className="form-select" value={roomType} onChange={(e) => setRoomType(e.target.value)}>
                    <option value="group">group</option>
                    <option value="direct">direct</option>
                    <option value="department">department</option>
                    <option value="broadcast">broadcast</option>
                  </select>
                  <div className="form-text">Allowed: direct, group, department, broadcast</div>
                </div>
                <div className="mb-3">
                  <label className="form-label">Participants (optional)</label>
                  <div style={{ maxHeight: 220, overflow: "auto", border: "1px solid #e9ecef", padding: 8, borderRadius: 6 }}>
                    {loadingUsers ? (
                      <div className="text-muted">Loading users...</div>
                    ) : allUsers.length === 0 ? (
                      <div className="text-muted">No users loaded. You can create the room and add participants later.</div>
                    ) : (
                      allUsers.map((u) => {
                        const id = u.id;
                        const checked = selectedParticipants.has(id);
                        return (
                          <div key={String(id)} className="form-check">
                            <input className="form-check-input" type="checkbox" id={`p-${id}`} checked={Boolean(checked)} onChange={() => toggleParticipant(id)} />
                            <label className="form-check-label" htmlFor={`p-${id}`}>{u.name} {String(getCurrentUserId()) === String(id) ? <small className="text-muted"> (you)</small> : null}</label>
                          </div>
                        );
                      })
                    )}
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-outline-secondary" onClick={() => setShowCreateModal(false)}> Cancel </button>
                <button type="submit" className="btn btn-primary" disabled={creatingRoom}> {creatingRoom ? "Creating..." : "Create"} </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showAddMemberModal && (
        <div className="modal show d-block" tabIndex="-1" role="dialog" style={{ background: "rgba(0,0,0,0.4)" }}>
          <div className="modal-dialog modal-lg" role="document">
            <form className="modal-content" onSubmit={submitAddMembersHandler}>
              <div className="modal-header">
                <h5 className="modal-title">Add / Manage Members</h5>
                <button type="button" className="btn-close" aria-label="Close" onClick={() => setShowAddMemberModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-2">
                  <strong>Room ID: {addMemberRoomId}</strong>
                </div>
                <div style={{ maxHeight: 360, overflow: "auto", border: "1px solid #e9ecef", padding: 8, borderRadius: 6 }}>
                  {loadingUsers ? (
                    <div className="text-muted">Loading users...</div>
                  ) : allUsers.length === 0 ? (
                    <div className="text-muted">No users available to add.</div>
                  ) : (
                    allUsers.map((u) => {
                      const id = u.id;
                      const checked = addMemberSelected.has(id);
                      return (
                        <div key={String(id)} className="form-check">
                          <input className="form-check-input" type="checkbox" id={`am-${id}`} checked={Boolean(checked)} onChange={() => toggleAddMember(id)} />
                          <label className="form-check-label" htmlFor={`am-${id}`}>{u.name} {String(getCurrentUserId()) === String(id) ? <small className="text-muted"> (you)</small> : null}</label>
                        </div>
                      );
                    })
                  )}
                </div>
                <div className="mt-2">
                  <small className="text-muted"> Checked users will be the room participants after save. Uncheck to remove participants (if backend supports it). </small>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-outline-secondary" onClick={() => setShowAddMemberModal(false)}> Cancel </button>
                <button type="submit" className="btn btn-primary" disabled={addingMembers}> {addingMembers ? "Saving..." : "Save participants"} </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showDetailsModal && (
        <div className="modal show d-block" tabIndex="-1" role="dialog" style={{ background: "rgba(0,0,0,0.4)" }}>
          <div className="modal-dialog modal-md" role="document">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Room Participants</h5>
                <button type="button" className="btn-close" aria-label="Close" onClick={() => setShowDetailsModal(false)}></button>
              </div>
              <div className="modal-body">
                <div className="mb-2">
                  <strong>{detailsRoom?.title ?? detailsRoom?.name ?? `Room ${detailsRoom?._id ?? detailsRoom?.id ?? ""}`}</strong>
                  <div className="small text-muted">ID: {detailsRoom?._id ?? detailsRoom?.id ?? detailsRoom?.room_id ?? ""}</div>
                </div>
                <div style={{ maxHeight: 300, overflow: "auto", border: "1px solid #e9ecef", padding: 8, borderRadius: 6 }}>
                  {detailsParticipants.length === 0 ? ( <div className="text-muted">No participants</div> ) : ( <ul className="list-unstyled mb-0"> {detailsParticipants.map((p) => ( <li key={String(p.id)} className="py-1 border-bottom"> {p.name} </li> ))} </ul> )}
                </div>
                <div className="mt-2">
                  <small className="text-muted"> If participant names show as IDs, load full users to resolve names. <button className="btn btn-link btn-sm p-0 ms-2" onClick={() => loadAllUsers()}> Load users </button> </small>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-outline-secondary" onClick={() => setShowDetailsModal(false)}> Close </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
