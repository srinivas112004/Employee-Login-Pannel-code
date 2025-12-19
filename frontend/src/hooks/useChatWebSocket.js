// src/hooks/useChatWebSocket.js
import { useCallback, useEffect, useRef, useState } from "react";

/**
 * useChatWebSocket
 * - Connects to ws://<host>/ws/chat/{roomId}/?token=...
 * - Reconnects with exponential backoff
 * - Falls back to periodic REST fetch if WS fails
 * - Supports token refresh using POST /api/auth/token/refresh/ (if available)
 *
 * API:
 *   const { messages, connected, sendMessage, sendTypingStart, sendTypingStop, sendReaction, markRead, lastError, reconnect } = useChatWebSocket({ base });
 *
 * Notes:
 * - Expects server message shapes similar to your Day13 backend:
 *    { type: 'message', data: {...} }
 *    { type: 'typing', user_id, username, is_typing }
 *    { type: 'reaction', message_id, emoji, user_id }
 *    { type: 'read_receipt', message_id, user_id }
 *    { type: 'online_users', users: [...] }   OR plain array of users
 *    { type: 'user_joined'/'user_left', user: {...} }
 */

const DEFAULT_POLL = 30000;
const MAX_BACKOFF = 30000;

function getHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  };
}

function buildWsBaseUrl(base, wsPath = "/ws/chat/") {
  try {
    const u = new URL(base);
    const proto = u.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${u.host}${wsPath}`;
  } catch (e) {
    return `ws://localhost:8000${wsPath}`;
  }
}

export default function useChatWebSocket({ base = (process.env.REACT_APP_API_BASE || "http://localhost:8000"), roomId, pollInterval = DEFAULT_POLL } = {}) {
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(false);
  const [lastError, setLastError] = useState(null);
  const [typingUsers, setTypingUsers] = useState([]); // optional for UI
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const backoff = useRef(1000);
  const pollTimer = useRef(null);
  const isUnmounted = useRef(false);
  const wsBase = buildWsBaseUrl(base, "/ws/chat/");

  // helpers to normalize messages order (oldest -> newest)
  const normalizeMessagesOrder = useCallback((list = []) => {
    if (!Array.isArray(list) || list.length === 0) return [];
    const getDate = (m) => new Date((m.created_at ?? m.timestamp ?? m.createdAt) || 0).getTime() || 0;
    return list.slice().sort((a, b) => getDate(a) - getDate(b));
  }, []);

  // REST fallback fetch for messages (used when WS fails)
  const restFetchMessages = useCallback(async (rId) => {
    if (!rId) return [];
    try {
      const res = await fetch(`${base.replace(/\/$/, "")}/api/chat/rooms/${rId}/messages/`, { headers: getHeaders() });
      if (!res.ok) throw new Error(`REST messages failed ${res.status}`);
      const body = await res.json().catch(() => null);
      const arr = Array.isArray(body) ? body : body?.results ?? [];
      return normalizeMessagesOrder(arr || []);
    } catch (err) {
      console.warn("useChatWebSocket.restFetchMessages error:", err);
      return [];
    }
  }, [base, normalizeMessagesOrder]);

  // token refresh helper (optional; only if /api/auth/token/refresh/ exists)
  const tryRefreshToken = useCallback(async () => {
    try {
      const refresh = localStorage.getItem("refresh_token");
      if (!refresh) throw new Error("no refresh token");
      const res = await fetch(`${base.replace(/\/$/, "")}/api/auth/token/refresh/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh }),
      });
      if (!res.ok) throw new Error("refresh failed");
      const data = await res.json().catch(() => null);
      if (data?.access) {
        localStorage.setItem("access_token", data.access);
        if (data.refresh) localStorage.setItem("refresh_token", data.refresh);
        return true;
      }
      return false;
    } catch (err) {
      console.warn("token refresh failed", err);
      return false;
    }
  }, [base]);

  const closeWs = useCallback(() => {
    try {
      if (wsRef.current) {
        wsRef.current.onopen = null;
        wsRef.current.onmessage = null;
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        try { wsRef.current.close(); } catch (_) {}
      }
    } catch (_) {}
    wsRef.current = null;
    setConnected(false);
  }, []);

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
  }, []);

  const startPolling = useCallback((rId) => {
    if (pollTimer.current) return;
    pollTimer.current = setInterval(async () => {
      if (!rId) return;
      const list = await restFetchMessages(rId);
      if (!isUnmounted.current) setMessages(list);
    }, pollInterval);
  }, [pollInterval, restFetchMessages]);

  const stopPolling = useCallback(() => {
    if (pollTimer.current) {
      clearInterval(pollTimer.current);
      pollTimer.current = null;
    }
  }, []);

  const scheduleReconnect = useCallback((rId) => {
    clearReconnectTimer();
    reconnectTimer.current = setTimeout(() => {
      if (!isUnmounted.current) connectWs({ forced: true, rId });
    }, backoff.current);
    backoff.current = Math.min(Math.round(backoff.current * 1.8), MAX_BACKOFF);
  }, [clearReconnectTimer]);

  // main connect function
  const connectWs = useCallback(async ({ forced = false, rId = roomId } = {}) => {
    // if already open and not forced -> skip
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && !forced) return;

    closeWs();
    clearReconnectTimer();
    stopPolling();

    if (!rId) {
      // nothing to connect to
      return;
    }

    const token = localStorage.getItem("access_token") || "";
    const url = token ? `${wsBase}${rId}/?token=${encodeURIComponent(token)}` : `${wsBase}${rId}/`;

    // small delay to let things settle
    setTimeout(() => {
      if (isUnmounted.current) return;
      let socket;
      try {
        socket = new WebSocket(url);
        wsRef.current = socket;
      } catch (err) {
        console.error("useChatWebSocket: WebSocket constructor failed", err);
        setLastError(err);
        // fallback to REST poll
        restFetchMessages(rId).then((list) => { if (!isUnmounted.current) setMessages(list); });
        startPolling(rId);
        scheduleReconnect(rId);
        return;
      }

      socket.onopen = () => {
        if (isUnmounted.current) return;
        console.info("useChatWebSocket: ws open", rId);
        setConnected(true);
        setLastError(null);
        backoff.current = 1000;
      };

      socket.onmessage = (ev) => {
        if (isUnmounted.current) return;
        try {
          const data = JSON.parse(ev.data);
          // If server sends an array of messages directly (initial batch)
          if (Array.isArray(data)) {
            setMessages((prev) => {
              // merge / replace strategy: prefer server batch
              return normalizeMessagesOrder(data);
            });
            return;
          }
          // Common structure: { type: 'message', data: { ... } }
          if (data?.type === "message" && data.data) {
            setMessages((prev) => normalizeMessagesOrder([...prev, data.data]));
            return;
          }
          // Some servers send { type: 'new_message', message: {...} }
          if ((data?.type === "new_message" || data?.type === "created_message") && data.message) {
            setMessages((prev) => normalizeMessagesOrder([...prev, data.message]));
            return;
          }
          if (data?.type === "typing") {
            // data: { user_id, username, is_typing }
            if (data.is_typing) {
              setTypingUsers((prev) => Array.from(new Set([...prev, data.username || data.user_id])));
            } else {
              setTypingUsers((prev) => prev.filter((x) => x !== (data.username || data.user_id)));
            }
            return;
          }
          if (data?.type === "reaction" && data.message_id) {
            // update message reactions in local state (best-effort)
            setMessages((prev) => prev.map((m) => {
              const id = m._id ?? m.id ?? m.pk ?? m.message_id ?? m.client_id;
              if (String(id) === String(data.message_id)) {
                const reactions = { ...(m.reactions || {}) };
                if (!reactions[data.emoji]) reactions[data.emoji] = [];
                if (!reactions[data.emoji].includes(data.user_id)) reactions[data.emoji].push(data.user_id);
                return { ...m, reactions };
              }
              return m;
            }));
            return;
          }
          if (data?.type === "read_receipt" && data.message_id) {
            setMessages((prev) => prev.map((m) => {
              const id = m._id ?? m.id ?? m.pk ?? m.message_id ?? m.client_id;
              if (String(id) === String(data.message_id)) {
                const read_by = Array.isArray(m.read_by) ? Array.from(new Set([...m.read_by, data.user_id])) : [data.user_id];
                return { ...m, read_by };
              }
              return m;
            }));
            return;
          }
          if (data?.type === "online_users" && Array.isArray(data.users)) {
            // ignore here; useOnlineStatus handles online users
            return;
          }
          // user_joined / user_left not handled here intentionally (UI-level)
        } catch (err) {
          console.warn("useChatWebSocket: failed parse ws message", err);
        }
      };

      socket.onerror = (ev) => {
        if (isUnmounted.current) return;
        console.error("useChatWebSocket ws error", ev);
        setLastError(new Error("WebSocket error"));
      };

      socket.onclose = async (ev) => {
        if (isUnmounted.current) return;
        console.warn("useChatWebSocket ws closed", ev.code, ev.reason);
        setConnected(false);

        // If closed with 4001/4002 (custom code), try token refresh (example)
        // Many backends use 4001 for auth; adjust per backend.
        if (ev.code === 4001 || ev.code === 4002) {
          const refreshed = await tryRefreshToken();
          if (refreshed) {
            // try reconnect immediately
            connectWs({ forced: true, rId });
            return;
          }
        }

        // fallback to REST fetch + polling
        restFetchMessages(rId).then((list) => { if (!isUnmounted.current) setMessages(list); });
        startPolling(rId);

        // schedule reconnect
        scheduleReconnect(rId);
      };
    }, 200);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [base, normalizeMessagesOrder, restFetchMessages, startPolling, scheduleReconnect, tryRefreshToken, wsBase, roomId]);

  // public API: send message via WS (fallback to REST)
  const sendMessage = useCallback(async ({ room = roomId, content, message_type = "text" } = {}) => {
    if (!room) throw new Error("no room");
    const payload = { room, content, message_type };
    // Use WS if open
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ type: "message", ...payload }));
        return { ok: true };
      } catch (err) {
        console.warn("ws send failed, falling back to REST", err);
      }
    }
    // fallback REST
    try {
      const res = await fetch(`${base.replace(/\/$/, "")}/api/chat/messages/`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const text = await (res.text().catch(() => null));
        throw new Error(`REST send failed ${res.status} ${text ?? ""}`);
      }
      const data = await res.json().catch(() => null);
      // append server message if present
      if (data) {
        setMessages((prev) => normalizeMessagesOrder([...prev, data]));
      } else {
        // reload messages
        const list = await restFetchMessages(room);
        setMessages(list);
      }
      return { ok: true };
    } catch (err) {
      console.error("sendMessage failed", err);
      setLastError(err);
      return { ok: false, error: err };
    }
  }, [base, normalizeMessagesOrder, restFetchMessages, roomId]);

  const sendTypingStart = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    try { wsRef.current.send(JSON.stringify({ type: "typing_start" })); }
    catch (e) {}
  }, []);

  const sendTypingStop = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    try { wsRef.current.send(JSON.stringify({ type: "typing_stop" })); }
    catch (e) {}
  }, []);

  const sendReaction = useCallback((messageId, emoji) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    try { wsRef.current.send(JSON.stringify({ type: "reaction", message_id: messageId, emoji })); }
    catch (e) { console.warn("sendReaction failed", e); }
  }, []);

  const markRead = useCallback(async (messageId) => {
    // Try WS first
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ type: "read_receipt", message_id: messageId }));
        return { ok: true };
      } catch (err) {
        console.warn("markRead ws send failed", err);
      }
    }
    // fallback REST
    try {
      const res = await fetch(`${base.replace(/\/$/, "")}/api/chat/messages/${messageId}/mark-read/`, {
        method: "POST",
        headers: getHeaders(),
      });
      if (!res.ok) throw new Error(`markRead failed ${res.status}`);
      return { ok: true };
    } catch (err) {
      console.warn("markRead failed", err);
      return { ok: false, error: err };
    }
  }, [base]);

  // reconnect helper
  const reconnect = useCallback(() => {
    clearReconnectTimer();
    closeWs();
    connectWs({ forced: true, rId: roomId });
  }, [clearReconnectTimer, closeWs, connectWs, roomId]);

  useEffect(() => {
    isUnmounted.current = false;
    // start connection when mounted / roomId changes
    connectWs({ forced: true, rId: roomId });

    // If WS doesn't open quickly, do a REST attempt and poll.
    const t = setTimeout(() => {
      if (!connected && !isUnmounted.current) {
        restFetchMessages(roomId).then((list) => { if (!isUnmounted.current) setMessages(list); });
        startPolling(roomId);
      }
    }, 900);

    return () => {
      isUnmounted.current = true;
      clearTimeout(t);
      clearReconnectTimer();
      stopPolling();
      closeWs();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roomId]);

  return {
    messages,
    setMessages,
    connected,
    lastError,
    typingUsers,
    sendMessage,
    sendTypingStart,
    sendTypingStop,
    sendReaction,
    markRead,
    reconnect,
  };
}
