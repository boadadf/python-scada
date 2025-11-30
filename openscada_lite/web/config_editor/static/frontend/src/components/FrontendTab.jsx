/*
SCADA Config Editor React App
Drop this file into: openscada_lite/web/config_editor/static/frontend/src/App.jsx

Build with your existing webpack setup (entry ./src/index.jsx imports App.jsx)

Features implemented:
- Top menu File: New, Load, Save, Upload
- Tabs: Modules, Datapoint Types, Drivers, Rules
- Each tab: top table with items, +/- buttons to add/delete
- Selecting a row shows a detail form below for editing
- Save button sends POST /config-editor/api/config
- Load uses GET /config-editor/api/config
- Upload calls POST /config-editor/api/reload

This is a single-file React implementation using fetch (no external libs).
Keep index.jsx as entry that mounts this App.
*/

import React, { useState, useEffect } from "react";

export default function FrontendTab({ config, setConfig }) {
  // Find the frontend module in config.modules
  const idx = (config.modules || []).findIndex(m => m.name === "frontend");
  const frontendModule = idx >= 0 ? config.modules[idx] : null;
  const [tabsText, setTabsText] = useState(
    frontendModule?.config?.tabs?.join("\n") || ""
  );

  useEffect(() => {
    setTabsText(frontendModule?.config?.tabs?.join("\n") || "");
  }, [frontendModule]);

  function handleTabsChange(e) {
    setTabsText(e.target.value);
    if (idx < 0) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.modules[idx].config.tabs = e.target.value
      .split("\n")
      .map(t => t.trim())
      .filter(Boolean);
    setConfig(copy);
  }

  if (!frontendModule) {
    return <div style={{ padding: 12, color: "red" }}>No frontend module found in config.</div>;
  }

  return (
    <div style={{ padding: 12 }}>
      <h3>Frontend Module Tabs Configuration</h3>
      <label>Tabs (one per line):</label>
      <textarea
        rows={8}
        style={{ width: "100%", fontFamily: "monospace", marginBottom: 8 }}
        value={tabsText}
        onChange={handleTabsChange}
      />
    </div>
  );
}