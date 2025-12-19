// src/hooks/useOnlineStatus.js
import { useEffect, useRef, useState, useCallback } from "react";

/**
 * Robust useOnlineStatus hook
 * - base: API base (e.g. "http://localhost:8000")
 * - pollInterval: REST poll fallback interval
 *
 * Exposes: { onlineUsers, connected, lastError, refresh, reconnect, close }
 */

const DEFAULT_POLL_INTERVAL = 30000; // 30s
const MAX_BACKOFF_MS = 30000;

const CANDIDATE_REST_PATHS = [
  "/api/chat/online-status/online-users/",
  "/api/chat/online-status/online-users",
  "/api/chat/online-status/",
  "/api/chat/online-status",
  "/api/online-status/online-users/",
  "/api/chat/online/",
];

function defaultGetHeaders() {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  };
}

function buildWsBaseUrl(base, wsPath = "/ws/online/") {
  try {
    const u = new URL(base);
    const proto = u.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${u.host}${wsPath}`;
  } catch (e) {
    // fallback
    return `ws://localhost:8000${wsPath}`;
  }
}

async function tryFetchCandidates(base, headers = {}) {
  let lastErr = null;
  for (const path of CANDIDATE_REST_PATHS) {
    const url = path.startsWith("http") ? path : `${base.replace(/\/$/, "")}${path}`;
    try {
      const res = await fetch(url, { headers });
      if (!res.ok) {
        lastErr = new Error(`REST ${url} failed status ${res.status}`);
        continue;
      }
      const body = await res.json().catch(() => null);
      if (!body) return [];
      const arr = Array.isArray(body) ? body : body.results ?? [];
      if (!Array.isArray(arr)) return [];
      return arr;
    } catch (err) {
      lastErr = err;
      continue;
    }
  }
  throw lastErr ?? new Error("No working REST endpoint found for online users");
}

export default function useOnlineStatus({ base = (process.env.REACT_APP_API_BASE || "http://localhost:8000"), pollInterval = DEFAULT_POLL_INTERVAL, getHeaders = defaultGetHeaders, wsPath = "/ws/online/" } = {}) {
  const [onlineUsers, setOnlineUsers] = useState([]);
  const [connected, setConnected] = useState(false);
  const [lastError, setLastError] = useState(null);

  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const pollTimerRef = useRef(null);
  const backoffRef = useRef(1000); // start 1s
  const isUnmountedRef = useRef(false);

  const wsBaseUrl = buildWsBaseUrl(base, wsPath);

  const restFetch = useCallback(async () => {
    try {
      const headers = getHeaders();
      const users = await tryFetchCandidates(base, headers);
      if (!isUnmountedRef.current) {
        setOnlineUsers(users || []);
        setLastError(null);
      }
      return users;
    } catch (err) {
      console.warn("useOnlineStatus.restFetch error:", err);
      if (!isUnmountedRef.current) setLastError(err);
      throw err;
    }
  }, [base, getHeaders]);

  const startPolling = useCallback(() => {
    if (pollTimerRef.current) return;
    pollTimerRef.current = setInterval(() => {
      restFetch().catch(() => {});
    }, pollInterval);
  }, [pollInterval, restFetch]);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const closeWs = useCallback(() => {
    try {
      if (wsRef.current) {
        wsRef.current.onopen = null;
        wsRef.current.onmessage = null;
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.close();
      }
    } catch (e) {}
    wsRef.current = null;
    setConnected(false);
  }, []);

  const connectWs = useCallback((opts = { forced: false }) => {
    // avoid duplicate when already open
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && !opts.forced) {
      console.debug("useOnlineStatus: ws already open");
      return;
    }

    closeWs();
    clearReconnectTimer();
    stopPolling();

    const token = localStorage.getItem("access_token") || "";
    const url = token ? `${wsBaseUrl}?token=${encodeURIComponent(token)}` : wsBaseUrl;

    console.debug("useOnlineStatus: attempting WS connect ->", url);

    // small delay to allow server / token refresh to complete
    const delayBeforeOpen = 250;
    setTimeout(() => {
      if (isUnmountedRef.current) return;

      let socket;
      try {
        socket = new WebSocket(url);
        wsRef.current = socket;
      } catch (err) {
        console.error("useOnlineStatus: WebSocket constructor failed", err);
        setLastError(err);
        // fallback to REST poll
        restFetch().catch(() => {});
        startPolling();
        // schedule reconnect
        clearReconnectTimer();
        reconnectTimerRef.current = setTimeout(() => {
          if (!isUnmountedRef.current) connectWs({ forced: true });
        }, backoffRef.current);
        backoffRef.current = Math.min(backoffRef.current * 1.8, MAX_BACKOFF_MS);
        return;
      }

      socket.onopen = () => {
        if (isUnmountedRef.current) return;
        console.info("useOnlineStatus: ws open");
        setConnected(true);
        setLastError(null);
        backoffRef.current = 1000; // reset backoff
      };

      socket.onmessage = (ev) => {
        if (isUnmountedRef.current) return;
        try {
          const data = JSON.parse(ev.data);
          if (Array.isArray(data)) {
            setOnlineUsers(data);
            return;
          }
          if (data?.type === "online_users" && Array.isArray(data.users)) {
            setOnlineUsers(data.users);
            return;
          }
          if (data?.type === "status_change" && data.user) {
            setOnlineUsers((prev) => {
              const uidOf = (u) => String(u.user_id ?? u.id ?? u.pk ?? u._id ?? "");
              const duid = uidOf(data.user);
              if (data.is_online) {
                if (prev.find((p) => uidOf(p) === duid)) return prev;
                return [...prev, data.user];
              } else {
                return prev.filter((p) => uidOf(p) !== duid);
              }
            });
            return;
          }
          if (Array.isArray(data.users)) {
            setOnlineUsers(data.users);
            return;
          }
          // otherwise ignore or console.log(data)
        } catch (err) {
          console.warn("useOnlineStatus: failed parse ws message", err);
        }
      };

      socket.onerror = (ev) => {
        if (isUnmountedRef.current) return;
        console.error("useOnlineStatus ws error", ev);
        setLastError(new Error("WebSocket error"));
      };

      socket.onclose = (ev) => {
        if (isUnmountedRef.current) return;
        console.warn("useOnlineStatus ws closed", ev.code, ev.reason);
        setConnected(false);
        // fallback REST fetch and polling
        restFetch().catch(() => {});
        startPolling();
        // schedule reconnect with exponential backoff
        clearReconnectTimer();
        reconnectTimerRef.current = setTimeout(() => {
          if (!isUnmountedRef.current) connectWs({ forced: true });
        }, backoffRef.current);
        backoffRef.current = Math.min(Math.round(backoffRef.current * 1.8), MAX_BACKOFF_MS);
      };
    }, delayBeforeOpen);
  }, [backoffRef, clearReconnectTimer, closeWs, restFetch, startPolling, stopPolling, wsBaseUrl]);

  const reconnect = useCallback(() => {
    clearReconnectTimer();
    closeWs();
    connectWs({ forced: true });
  }, [clearReconnectTimer, closeWs, connectWs]);

  const refresh = useCallback(() => {
    return restFetch();
  }, [restFetch]);

  useEffect(() => {
    isUnmountedRef.current = false;
    // try WS first
    connectWs();

    // if WS doesn't open quickly, do one REST attempt then poll
    const t = setTimeout(() => {
      if (!connected && !isUnmountedRef.current) {
        restFetch().catch(() => {});
        startPolling();
      }
    }, 900);

    return () => {
      isUnmountedRef.current = true;
      clearTimeout(t);
      clearReconnectTimer();
      stopPolling();
      closeWs();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    onlineUsers,
    connected,
    lastError,
    refresh,
    reconnect,
    close: closeWs,
  };
}
