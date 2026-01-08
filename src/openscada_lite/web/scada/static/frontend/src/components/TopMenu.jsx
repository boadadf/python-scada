import React, { useState, useRef } from "react";
import { useAuth } from "login";
import { usePing } from "../contexts/PingContext";

export default function TopMenu() {
  const [open, setOpen] = useState(false);
  const menuRef = useRef();
  const { logout } = useAuth();
  const { user } = useAuth();
  const { serverTimestamp } = usePing();

  function handleLogout() {
    setOpen(false);
    logout();
    window.location.href = "/scada";
  }

  function handleAbout() {
    setOpen(false);
    window.open("/static/README.html", "_blank");
  }

  return (
    <div
      className="osl-topmenu"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0.5em 1em",
        background: "#f5f5f5",
        borderBottom: "1px solid #ddd",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "2em" }}>
        <div
          className="osl-topmenu-title"
          style={{ fontWeight: "bold", fontSize: "1.2em" }}
        >
          OSL Open Scada Lite
        </div>
        <div
          className="osl-topmenu-info"
          style={{ fontSize: "0.95em", display: "flex", gap: "1em" }}
        >
          <span>User: <b>{user || "Unknown"}</b></span>
          <span>Server time: <b>{serverTimestamp}</b></span>
        </div>
      </div>
      <div ref={menuRef} className="osl-topmenu-operations">
        <button
          className="osl-topmenu-operations-btn"
          onClick={() => setOpen(v => !v)}
        >
          Operations ▾
        </button>
        {open && (
          <div className="osl-topmenu-dropdown">
            <div
              className="osl-topmenu-dropdown-item"
              onClick={handleLogout}
            >Logout</div>
            <div
              className="osl-topmenu-dropdown-item"
              onClick={handleAbout}
            >About</div>
          </div>
        )}
      </div>
    </div>
  );
}