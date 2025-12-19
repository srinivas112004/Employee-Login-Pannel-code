// src/components/OnlineUsers.jsx
import React from "react";
import useOnlineStatus from "../hooks/useOnlineStatus";

export default function OnlineUsers({ base }) {
  const { onlineUsers, connected, lastError, refresh } = useOnlineStatus({ base });

  return (
    <div style={{ padding: 12 }}>
      <div className="d-flex justify-content-between align-items-center mb-2">
        <h6 className="mb-0">Online</h6>
        <button className="btn btn-sm btn-outline-secondary" onClick={() => refresh()}>Refresh</button>
      </div>
      {connected ? (
        <ul className="list-unstyled small" style={{ maxHeight: 220, overflow: "auto" }}>
          {onlineUsers.map((u, idx) => {
            const id = String(u._id ?? u.id ?? u.user_id ?? idx);
            const name = (u.user?.username || u.username || u.full_name || u.name || (u.email ? String(u.email).split("@")[0] : `User ${id}`));
            return (
              <li key={id} className="d-flex align-items-center gap-2 mb-1">
                <span className="badge bg-success rounded-circle" style={{ width: 8, height: 8, padding: 0 }} />
                <span>{name}</span>
              </li>
            );
          })}
        </ul>
      ) : (
        <div className="text-muted">Connecting... {lastError ? String(lastError) : null}</div>
      )}
    </div>
  );
}
