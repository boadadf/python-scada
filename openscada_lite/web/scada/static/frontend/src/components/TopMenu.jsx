import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "login";

export default function TopMenu() {
  const [open, setOpen] = useState(false);
  const menuRef = useRef();
  const { logout } = useAuth();

  useEffect(() => {
    function handleClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  function handleLogout() {
    setOpen(false);
    logout();
    window.location.href = "/scada";
  }


  function handleAbout() {
    setOpen(false);
    window.open("/static/README.html", "_blank"); // Open README.html in a new tab
  }

  return (
    <div className="osl-topmenu">
      <div className="osl-topmenu-title">
        OSL Open Scada Lite
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