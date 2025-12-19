// src/components/MessageSearch.jsx
import React, { useState } from "react";
import axios from "axios";

export default function MessageSearch({ roomId, base = (process.env.REACT_APP_API_BASE || "http://localhost:8000") }) {
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const token = localStorage.getItem("access_token");

  const search = async () => {
    if (!q || q.trim().length < 2) return;
    setLoading(true);
    try {
      const res = await axios.get(`${base.replace(/\/$/, "")}/api/chat/messages/search/`, {
        params: { room: roomId, q },
        headers: { Authorization: `Bearer ${token}` },
      });
      setResults(res.data?.results ?? res.data ?? []);
    } catch (err) {
      console.error("Message search failed", err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="d-flex mb-2">
        <input className="form-control form-control-sm" placeholder="Search messages..." value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && search()} />
        <button className="btn btn-sm btn-secondary ms-2" onClick={search} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      <div style={{ maxHeight: 200, overflow: "auto" }}>
        {results.map((r) => (
          <div key={String(r.id ?? r._id ?? Math.random())} className="p-2 border-bottom">
            <div><strong>{r.sender?.first_name ?? r.sender_name ?? r.sender?.username}</strong></div>
            <div>{r.content}</div>
            <small className="text-muted">{r.created_at ?? r.timestamp}</small>
          </div>
        ))}
      </div>
    </div>
  );
}
