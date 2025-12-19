// src/components/Message.jsx
import React from "react";
import { FaEdit, FaTrash, FaCheckDouble } from "react-icons/fa";
import { format } from "date-fns";

export default function Message({
  message,
  isOwner = false,
  onEdit = () => {},
  onDelete = () => {},
  onMarkRead = () => {},
}) {
  const id = String(message._id ?? message.id ?? message.pk ?? Math.random());
  const content = message.content ?? message.message ?? "";
  const sender = message.sender_name ?? message.sender?.username ?? message.sender?.email ?? message.sender ?? "User";
  const ts = message.created_at ?? message.timestamp ?? message.createdAt;

  return (
    <div key={id} className="mb-3 p-3" style={{ borderRadius: 8, background: "#fff", boxShadow: "0 1px 2px rgba(0,0,0,0.03)" }}>
      <div className="d-flex justify-content-between align-items-start">
        <div>
          <strong>{sender}</strong>
          <div className="small text-muted">{ts ? format(new Date(ts), "PPP p") : ""}</div>
        </div>

        <div>
          {isOwner && (
            <>
              <button className="btn btn-sm btn-link p-0 me-2" title="Edit" onClick={() => onEdit(id, content)}>
                <FaEdit />
              </button>
              <button className="btn btn-sm btn-link p-0 me-2" title="Delete" onClick={() => onDelete(id)}>
                <FaTrash />
              </button>
              <button className="btn btn-sm btn-link p-0" title="Mark read" onClick={() => onMarkRead(id)}>
                <FaCheckDouble />
              </button>
            </>
          )}
        </div>
      </div>

      <div className="mt-2">{content}</div>
    </div>
  );
}
