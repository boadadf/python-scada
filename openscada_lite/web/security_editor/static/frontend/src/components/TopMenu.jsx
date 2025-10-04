import React, { useState, useRef, useEffect } from "react";

export default function TopMenu({ onLoad, onSave }) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef();

  // Close menu when clicking outside
  useEffect(() => {
    function handleClick(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setOpen(false);
    }
    if (open) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '8px 12px',
      borderBottom: '1px solid #ddd',
      background: '#f7f7f7',
      position: 'relative'
    }}>
      <div style={{ fontWeight: 'bold', fontSize: 18, letterSpacing: 1 }}>
        Security Config Editor
      </div>
      <div ref={menuRef} style={{ position: 'relative' }}>
        <button
          style={{
            background: 'none',
            border: 'none',
            fontWeight: 'bold',
            fontSize: 16,
            cursor: 'pointer',
            padding: '4px 12px'
          }}
          onClick={() => setOpen(v => !v)}
        >
          Operations ▾
        </button>
        {open && (
          <div style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            background: '#fff',
            border: '1px solid #ccc',
            borderRadius: 4,
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            zIndex: 10,
            minWidth: 140
          }}>
            <div
              style={{ padding: '8px 16px', cursor: 'pointer' }}
              onClick={() => { setOpen(false); onLoad(); }}
            >Load</div>
            <div
              style={{ padding: '8px 16px', cursor: 'pointer' }}
              onClick={() => { setOpen(false); onSave(); }}
            >Save</div>            
          </div>
        )}
      </div>
    </div>
  );
}