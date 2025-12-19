// src/components/OnlineUsersList.jsx
import React from "react";
import useOnlineStatus from "../hooks/useOnlineStatus";

export default function OnlineUsersList({ base }) {
  const { onlineUsers, connected, lastError, refresh, reconnect } = useOnlineStatus({ base });

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-2">
        <h6 className="mb-0">Online</h6>
        <small className="text-muted">{onlineUsers.length}</small>
      </div>

      <div className="mb-2">
        <small className={connected ? "text-success" : lastError ? "text-danger" : "text-muted"}>
          {connected ? "Connected" : lastError ? `Error` : "Connecting..."}
        </small>
        {lastError && <div className="small text-muted">{String(lastError.message ?? lastError)}</div>}
      </div>

      <ul className="list-unstyled small mb-3" style={{ maxHeight: 160, overflow: "auto" }}>
        {onlineUsers.map((u) => {
          const id = String(u._id ?? u.id ?? u.pk ?? u.user_id ?? Math.random());
          const name =
            (u.user && (u.user.full_name || u.user.username || u.user.email)) ||
            u.full_name ||
            u.username ||
            (u.email ? String(u.email).split("@")[0] : `User ${id}`);
          return (
            <li key={id} className="d-flex align-items-center gap-2 mb-1">
              <span className="badge bg-success rounded-circle" style={{ width: 8, height: 8, padding: 0 }} />
              <span>{name}</span>
            </li>
          );
        })}
      </ul>

      <div className="d-flex gap-2">
        <button className="btn btn-sm btn-outline-secondary" onClick={() => refresh()}>
          Refresh (REST)
        </button>
        <button className="btn btn-sm btn-outline-secondary" onClick={() => reconnect()}>
          Reconnect WS
        </button>
      </div>
    </div>
  );
}
