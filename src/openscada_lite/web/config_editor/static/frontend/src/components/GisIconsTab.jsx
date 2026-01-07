import React, { useState } from "react";
import Table from "./Table";

export default function GisIconsTab({ config, setConfig }) {
  const gisIcons = config.gis_icons || [];
  const [selectedIdx, setSelectedIdx] = useState(null);

  function saveConfig(copy) {
    setConfig(copy);
  }

  function addIcon() {
    const copy = structuredClone(config);
    if (!copy.gis_icons) copy.gis_icons = [];
    copy.gis_icons.push({
      id: "",
      icon: "",
      latitude: 0,
      longitude: 0,
      label: "",
      navigation: "",
      datapoint: "",
      rule_id: "",
      text: "", // Add default value for text
      states: {},
      alarm: {}
    });
    saveConfig(copy);
    setSelectedIdx(copy.gis_icons.length - 1);
  }

  function removeIcon() {
    if (selectedIdx == null) return;
    if (!window.confirm("Delete selected GIS icon?")) return;
    const copy = structuredClone(config);
    copy.gis_icons.splice(selectedIdx, 1);
    saveConfig(copy);
    setSelectedIdx(null);
  }

  function updateField(idx, field, value) {
    const copy = structuredClone(config);
    copy.gis_icons[idx][field] = value;
    saveConfig(copy);
  }

  function updateStates(idx, key, value) {
    const copy = structuredClone(config);
    if (!copy.gis_icons[idx].states) copy.gis_icons[idx].states = {};
    copy.gis_icons[idx].states[key] = value;
    saveConfig(copy);
  }

  function removeState(idx, key) {
    const copy = structuredClone(config);
    if (copy.gis_icons[idx].states) {
      delete copy.gis_icons[idx].states[key];
      saveConfig(copy);
    }
  }

  function addState(idx) {
    const key = prompt("State key:");
    if (!key) return;
    const value = prompt("Icon path for state:");
    if (value == null) return;
    updateStates(idx, key, value);
  }

  function updateAlarm(idx, key, value) {
    const copy = structuredClone(config);
    if (!copy.gis_icons[idx].alarm) copy.gis_icons[idx].alarm = {};
    copy.gis_icons[idx].alarm[key] = value;
    saveConfig(copy);
  }

  function removeAlarm(idx, key) {
    const copy = structuredClone(config);
    if (copy.gis_icons[idx].alarm) {
      delete copy.gis_icons[idx].alarm[key];
      saveConfig(copy);
    }
  }

  function addAlarm(idx) {
    const key = prompt("Alarm key:");
    if (!key) return;
    const value = prompt("Icon path for alarm:");
    if (value == null) return;
    updateAlarm(idx, key, value);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table
            columns={["id", "label", "latitude", "longitude"]}
            data={gisIcons.map(icon => ({
              id: icon.id,
              label: icon.label,
              latitude: icon.latitude,
              longitude: icon.longitude
            }))}
            selectedIndex={selectedIdx}
            onSelect={setSelectedIdx}
          />
        </div>
        <div style={{ width: 120, display: "flex", flexDirection: "column", gap: 6 }}>
          <button onClick={addIcon}>+</button>
          <button onClick={removeIcon} disabled={selectedIdx == null}>-</button>
        </div>
      </div>

      {selectedIdx != null && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit GIS Icon</h3>
          <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 8 }}>
            <tbody>
              {[
                ["id", "ID"],
                ["icon", "Icon Path"],
                ["label", "Label"],
                ["latitude", "Latitude"],
                ["longitude", "Longitude"],
                ["navigation", "Navigation"],
                ["datapoint", "Datapoint"],
                ["rule_id", "Rule ID"],
                ["text", "Text"] // Add text field
              ].map(([field, label]) => (
                <tr key={field}>
                  <td style={{ width: 120, padding: "0 8px" }}>{label}</td>
                  <td style={{ width: 320, padding: "0 8px" }}>
                    <input
                      value={gisIcons[selectedIdx][field] ?? ""}
                      onChange={e => updateField(selectedIdx, field,
                        field === "latitude" || field === "longitude"
                          ? Number(e.target.value)
                          : e.target.value
                      )}
                      style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                    />
                  </td>
                </tr>
              ))}
              <tr>
                <td style={{ verticalAlign: "top", padding: "0 8px" }}>States</td>
                <td>
                  {gisIcons[selectedIdx].states &&
                    Object.entries(gisIcons[selectedIdx].states).map(([k, v]) => (
                      <div key={k} style={{ display: "flex", gap: 8, marginBottom: 4 }}>
                        <input
                          value={k}
                          readOnly
                          style={{ width: 80, background: "#eee" }}
                        />
                        <input
                          value={v}
                          onChange={e => updateStates(selectedIdx, k, e.target.value)}
                          style={{ width: 220 }}
                        />
                        <button onClick={() => removeState(selectedIdx, k)}>Del</button>
                      </div>
                    ))}
                  <button onClick={() => addState(selectedIdx)}>+ state</button>
                </td>
              </tr>
              <tr>
                <td style={{ verticalAlign: "top", padding: "0 8px" }}>Alarm</td>
                <td>
                  {gisIcons[selectedIdx].alarm &&
                    Object.entries(gisIcons[selectedIdx].alarm).map(([k, v]) => (
                      <div key={k} style={{ display: "flex", gap: 8, marginBottom: 4 }}>
                        <input
                          value={k}
                          readOnly
                          style={{ width: 80, background: "#eee" }}
                        />
                        <input
                          value={v}
                          onChange={e => updateAlarm(selectedIdx, k, e.target.value)}
                          style={{ width: 220 }}
                        />
                        <button onClick={() => removeAlarm(selectedIdx, k)}>Del</button>
                      </div>
                    ))}
                  <button onClick={() => addAlarm(selectedIdx)}>+ alarm</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}