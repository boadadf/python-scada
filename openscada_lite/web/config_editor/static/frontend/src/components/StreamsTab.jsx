import React, { useState, useEffect } from "react";
import Table from "./Table";

export default function StreamsTab({ config, setConfig }) {
  const [selectedKey, setSelectedKey] = useState(null);
  const [editingStream, setEditingStream] = useState(null);

  const streams = config.streams || [];
  const keys = streams.map((s, i) => i);

  // Keep selected key valid
  useEffect(() => {
    if (selectedKey !== null && !keys.includes(selectedKey)) {
      setSelectedKey(null);
      setEditingStream(null);
    }
  }, [keys, selectedKey]);

  // Update editingStream when selection changes
  useEffect(() => {
    if (selectedKey !== null && streams[selectedKey]) {
      setEditingStream({ ...streams[selectedKey] });
    } else {
      setEditingStream(null);
    }
  }, [selectedKey, streams]);

  function saveStream() {
    if (selectedKey === null || !editingStream) return;
    const copy = structuredClone(config);
    copy.streams[selectedKey] = editingStream;
    setConfig(copy);
  }

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
    setEditingStream((prev) => ({ ...prev, [field]: value }));
  }

  if (!editingStream) return (
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
    </div>
  );

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

      <div style={{ marginTop: 12 }}>
        <h3>Edit Stream: {editingStream.description}</h3>
        <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 8 }}>
          <label>Description:</label>
          <input
            value={editingStream.description}
            onChange={(e) => updateField("description", e.target.value)}
            onBlur={saveStream}
          />

          <label>Server:</label>
          <input
            value={editingStream.server}
            onChange={(e) => updateField("server", e.target.value)}
            onBlur={saveStream}
            placeholder="Leave empty for same origin"
          />

          <label>Port:</label>
          <input
            type="text"
            value={editingStream.port}
            onChange={(e) => updateField("port", e.target.value)}
            onBlur={saveStream}
          />

          <label>Protocol:</label>
          <select
            value={editingStream.protocol}
            onChange={(e) => updateField("protocol", e.target.value)}
            onBlur={saveStream}
          >
            <option value="http">http</option>
            <option value="https">https</option>
          </select>

          <label>Path:</label>
          <input
            value={editingStream.path}
            onChange={(e) => updateField("path", e.target.value)}
            onBlur={saveStream}
            placeholder="e.g., feed1.m3u8"
          />
        </div>
      </div>
    </div>
  );
}
