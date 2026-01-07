import React, { useState, useEffect } from "react";
import Table from "./Table";

export default function StreamsTab({ config, setConfig }) {
  const [selectedKey, setSelectedKey] = useState(null);
  const streams = config.streams || [];
  const keys = streams.map((stream, index) => index);

  useEffect(() => {
    if (selectedKey !== null && !keys.includes(selectedKey)) {
      setSelectedKey(null);
    }
  }, [keys, selectedKey]);

  function addStream() {
    const name = prompt("New stream name (e.g., Camera 1):");
    if (!name) return;

    const copy = structuredClone(config);
    if (!copy.streams) copy.streams = [];
    copy.streams.push({
      id: `stream_${copy.streams.length + 1}`,
      description: name,
      server: "",
      port: "8090",
      protocol: "http",
      path: "",
    });
    setConfig(copy);
    setSelectedKey(copy.streams.length - 1);
  }

  function removeStream() {
    if (selectedKey === null) return;
    if (!window.confirm("Delete selected stream?")) return;

    const copy = structuredClone(config);
    copy.streams.splice(selectedKey, 1);
    setConfig(copy);
    setSelectedKey(null);
  }

  function updateField(field, value) {
    if (selectedKey === null) return;

    const copy = structuredClone(config);
    copy.streams[selectedKey][field] = value;
    setConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table
            columns={["description", "server", "port", "protocol", "path"]}
            data={streams}
            selectedIndex={selectedKey}
            onSelect={(i) => setSelectedKey(i)}
          />
        </div>
        <div style={{ width: 120, display: "flex", flexDirection: "column", gap: 6 }}>
          <button onClick={addStream}>+</button>
          <button onClick={removeStream} disabled={selectedKey === null}>
            -
          </button>
        </div>
      </div>

      {selectedKey !== null && streams[selectedKey] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Stream: {streams[selectedKey].description}</h3>
          <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 8 }}>
            <label>Description:</label>
            <input
              value={streams[selectedKey].description || ""}
              onChange={(e) => updateField("description", e.target.value)}
            />

            <label>Server:</label>
            <input
              value={streams[selectedKey].server || ""}
              onChange={(e) => updateField("server", e.target.value)}
              placeholder="Leave empty for same origin"
            />

            <label>Port:</label>
            <input
              type="text"
              value={streams[selectedKey].port || ""}
              onChange={(e) => updateField("port", e.target.value)}
            />

            <label>Protocol:</label>
            <select
              value={streams[selectedKey].protocol || "http"}
              onChange={(e) => updateField("protocol", e.target.value)}
            >
              <option value="http">http</option>
              <option value="https">https</option>
            </select>

            <label>Path:</label>
            <input
              value={streams[selectedKey].path || ""}
              onChange={(e) => updateField("path", e.target.value)}
              placeholder="e.g., feed1.m3u8"
            />
          </div>
        </div>
      )}
    </div>
  );
}