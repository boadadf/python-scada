import React, { useState, useEffect } from "react";

export default function SchedulerTab({ config, setConfig }) {
  // Find the schedule module config
  const module = (config.modules || []).find(m => m.name === "schedule");
  const schedules = module?.config?.schedules || [];
  const [selectedIdx, setSelectedIdx] = useState(null);
  const [editing, setEditing] = useState(null);

  useEffect(() => {
    if (selectedIdx !== null && schedules[selectedIdx]) {
      setEditing({ ...schedules[selectedIdx] });
    } else {
      setEditing(null);
    }
  }, [selectedIdx, schedules]);

  function saveSchedule() {
    if (selectedIdx === null || !editing) return;
    const copy = structuredClone(config);
    const mod = copy.modules.find(m => m.name === "schedule");
    mod.config.schedules[selectedIdx] = editing;
    setConfig(copy);
  }

  function addSchedule() {
    const copy = structuredClone(config);
    const mod = copy.modules.find(m => m.name === "schedule");
    if (!mod.config.schedules) mod.config.schedules = [];
    mod.config.schedules.push({
      schedule_id: "new_schedule",
      cron: "0 0 * * *",
      actions: []
    });
    setConfig(copy);
    setSelectedIdx(mod.config.schedules.length - 1);
  }

  function removeSchedule() {
    if (selectedIdx === null) return;
    if (!window.confirm("Delete selected schedule?")) return;
    const copy = structuredClone(config);
    const mod = copy.modules.find(m => m.name === "schedule");
    mod.config.schedules.splice(selectedIdx, 1);
    setConfig(copy);
    setSelectedIdx(null);
  }

  function updateField(field, value) {
    setEditing(prev => ({ ...prev, [field]: value }));
  }

  function updateAction(idx, value) {
    setEditing(prev => {
      const actions = [...prev.actions];
      actions[idx] = value;
      return { ...prev, actions };
    });
  }

  function addAction() {
    setEditing(prev => ({
      ...prev,
      actions: [...(prev.actions || []), ""]
    }));
  }

  function removeAction(idx) {
    setEditing(prev => ({
      ...prev,
      actions: prev.actions.filter((_, i) => i !== idx)
    }));
  }

  if (!module) return <div style={{ padding: 12 }}>No schedule module found in config.</div>;

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ borderBottom: "1px solid #ccc" }}>Schedule ID</th>
                <th style={{ borderBottom: "1px solid #ccc" }}>Cron</th>
                <th style={{ borderBottom: "1px solid #ccc" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {schedules.map((s, i) => (
                <tr
                  key={s.schedule_id}
                  style={{
                    background: selectedIdx === i ? "#e3f2fd" : undefined,
                    cursor: "pointer"
                  }}
                  onClick={() => setSelectedIdx(i)}
                >
                  <td>{s.schedule_id}</td>
                  <td>{s.cron}</td>
                  <td>{(s.actions || []).length}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ width: 120, display: "flex", flexDirection: "column", gap: 6 }}>
          <button onClick={addSchedule}>+</button>
          <button onClick={removeSchedule} disabled={selectedIdx === null}>-</button>
        </div>
      </div>
      {editing && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Schedule: {editing.schedule_id}</h3>
          <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 8 }}>
            <label>Schedule ID:</label>
            <input
              value={editing.schedule_id}
              onChange={e => updateField("schedule_id", e.target.value)}
              onBlur={saveSchedule}
            />
            <label>Cron:</label>
            <input
              value={editing.cron}
              onChange={e => updateField("cron", e.target.value)}
              onBlur={saveSchedule}
              placeholder="e.g. 0 17 * * *"
            />
            <label>Actions:</label>
            <div>
              {(editing.actions || []).map((a, idx) => (
                <div key={idx} style={{ display: "flex", gap: 4, marginBottom: 4 }}>
                  <input
                    style={{ flex: 1 }}
                    value={a}
                    onChange={e => updateAction(idx, e.target.value)}
                    onBlur={saveSchedule}
                  />
                  <button onClick={() => removeAction(idx)}>-</button>
                </div>
              ))}
              <button onClick={addAction}>Add Action</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}