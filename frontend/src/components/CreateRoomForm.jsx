// src/components/CreateRoomForm.jsx
import React, { useEffect, useState } from "react";

export default function CreateRoomForm({ base = (process.env.REACT_APP_API_BASE || "http://localhost:8000"), onCreated = () => {} }) {
  const [name, setName] = useState("");
  const [type, setType] = useState("group");
  const [users, setUsers] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    async function load() {
      setLoadingUsers(true);
      try {
        const res = await fetch(`${base.replace(/\/$/, "")}/api/auth/users/`, { headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` } });
        if (!res.ok) throw new Error("users load failed");
        const data = await res.json().catch(() => null);
        const arr = Array.isArray(data) ? data : data?.results ?? [];
        setUsers(arr.map(u => ({ id: u.id ?? u._id ?? u.pk, name: u.full_name || u.username || u.email })));
      } catch (err) {
        setUsers([]);
      } finally {
        setLoadingUsers(false);
      }
    }
    load();
  }, [base]);

  const toggle = (id) => {
    setSelected(prev => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    try {
      const payload = { name, room_type: type, participants: Array.from(selected) };
      const res = await fetch(`${base.replace(/\/$/, "")}/api/chat/rooms/`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("access_token")}` }, body: JSON.stringify(payload) });
      if (!res.ok) throw new Error("create failed");
      const created = await res.json().catch(()=>null);
      onCreated(created);
      setName("");
      setType("group");
      setSelected(new Set());
      alert("Room created");
    } catch (err) {
      console.error(err);
      alert("Create failed");
    } finally {
      setCreating(false);
    }
  };

  return (
    <form onSubmit={submit}>
      <div className="mb-2">
        <input className="form-control" placeholder="Room name" value={name} onChange={e => setName(e.target.value)} />
      </div>
      <div className="mb-2">
        <select className="form-select" value={type} onChange={e => setType(e.target.value)}>
          <option value="group">group</option>
          <option value="direct">direct</option>
          <option value="department">department</option>
          <option value="broadcast">broadcast</option>
        </select>
      </div>

      <div style={{ maxHeight: 180, overflow: "auto", border: "1px solid #eee", padding: 8 }} className="mb-2">
        {loadingUsers ? <div className="text-muted">Loading users...</div> : users.map(u => (
          <div key={String(u.id)} className="form-check">
            <input id={`p-${u.id}`} className="form-check-input" type="checkbox" checked={selected.has(u.id)} onChange={() => toggle(u.id)} />
            <label className="form-check-label" htmlFor={`p-${u.id}`}>{u.name}</label>
          </div>
        ))}
      </div>

      <div className="d-flex gap-2">
        <button className="btn btn-primary" type="submit" disabled={creating}>{creating ? "Creating..." : "Create"}</button>
      </div>
    </form>
  );
}
