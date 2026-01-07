import React from "react";

export default function Tabs({ tabs, active, onChange }) {
  return (
    <div style={{ display: 'flex', borderBottom: '1px solid #ddd' }}>
      {tabs.map(t => (
        <div key={t} onClick={() => onChange(t)} style={{ padding: '10px 14px', cursor: 'pointer', background: active === t ? '#fff' : '#f0f0f0', borderTop: '1px solid #ddd', borderLeft: '1px solid #ddd', borderRight: '1px solid #ddd' }}>{t}</div>
      ))}
    </div>
  );
}