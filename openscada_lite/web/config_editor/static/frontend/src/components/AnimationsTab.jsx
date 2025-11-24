import React, { useState, useEffect } from "react";
import Table from "./Table";

/**
 * AnimationTab.jsx
 *
 * - trigger_type: "datapoint" | "alarm" | "connection"
 * - Expression for alarm entries is stored as an object:
 *   { "ACTIVE": "<value-for-active>", "INACTIVE": "<value-for-inactive>", "FINISHED": ..., "ACK": ... }
 * - Expression for communication entries: { "ONLINE": "<value>", "OFFLINE": "<value>" }
 */

export default function AnimationTab({ config, setConfig }) {
  const [selectedKey, setSelectedKey] = useState(null);
  const [expressionModes, setExpressionModes] = useState({}); // 'eval' | 'mapping' | 'alarm'
  const animations = config.animations || {};
  const keys = Object.keys(animations);

  useEffect(() => {
    if (!selectedKey) return;
    const newModes = {};
    (animations[selectedKey] || []).forEach((entry, idx) => {
      if (entry.trigger_type === "alarm") {
        newModes[idx] = "alarm";
      } else {
        newModes[idx] = typeof entry.expression === "object" ? "mapping" : "eval";
      }
    });
    setExpressionModes(newModes);
  }, [selectedKey, animations]);

  function saveConfig(copy) {
    setConfig(copy);
  }

  function addAnimationGroup() {
    const name = prompt("New animation name:");
    if (!name) return;
    const copy = structuredClone(config);
    if (!copy.animations) copy.animations = {};
    copy.animations[name] = [];
    saveConfig(copy);
    setSelectedKey(name);
  }

  function removeAnimationGroup() {
    if (!selectedKey) return;
    if (!window.confirm("Delete selected animation group?")) return;
    const copy = structuredClone(config);
    delete copy.animations[selectedKey];
    saveConfig(copy);
    setSelectedKey(null);
  }

  function addEntry() {
    if (!selectedKey) return;
    const copy = structuredClone(config);
    const newEntry = {
      trigger_type: "datapoint",
      attribute: "",
      quality: { unknown: "" },
      expression: "",          // string or object
      duration: 0.5,
      default: "",
      revertAfter: 0
    };
    copy.animations[selectedKey].push(newEntry);
    saveConfig(copy);
    setExpressionModes(prev => ({ ...prev, [copy.animations[selectedKey].length - 1]: "eval" }));
  }

  function removeEntry(idx) {
    if (!selectedKey) return;
    const copy = structuredClone(config);
    copy.animations[selectedKey].splice(idx, 1);
    saveConfig(copy);
    setExpressionModes(prev => {
      const nm = { ...prev };
      delete nm[idx];
      return nm;
    });
  }

  function updateEntryField(idx, field, rawValue) {
    if (!selectedKey) return;
    const copy = structuredClone(config);
    const entry = copy.animations[selectedKey][idx];

    if (field === "duration" || field === "revert_after") {
      entry[field] = rawValue === "" ? 0 : Number(rawValue);
    } else if (field === "quality") {
      if (!entry.quality) entry.quality = {};
      entry.quality.unknown = rawValue;
    } else if (field === "trigger_type") {
      entry.trigger_type = rawValue;
      if (rawValue === "alarm") {
        setExpressionModes(prev => ({ ...prev, [idx]: "alarm" }));
        if (!entry.expression || typeof entry.expression !== "object") {
          entry.expression = { ACTIVE: "", INACTIVE: "", FINISHED: "", ACK: "" };
        }
      } else if (rawValue === "connection") {
        setExpressionModes(prev => ({ ...prev, [idx]: "alarm" })); // reuse alarm mode for simplicity
        if (!entry.expression || typeof entry.expression !== "object") {
          entry.expression = { ONLINE: "", OFFLINE: "" };
        }
      } else {
        setExpressionModes(prev => ({ ...prev, [idx]: typeof entry.expression === "object" ? "mapping" : "eval" }));
      }
    } else if (field === "expression") {
      const mode = expressionModes[idx];
      if (mode === "mapping") {
        try {
          entry.expression = JSON.parse(rawValue);
        } catch {
          entry.expression = {};
        }
      } else {
        entry.expression = rawValue;
      }
    } else {
      entry[field] = rawValue;
    }

    saveConfig(copy);
  }

  function updateAlarmExpression(idx, which, value) {
    if (!selectedKey) return;
    const copy = structuredClone(config);
    const entry = copy.animations[selectedKey][idx];
    if (!entry.expression || typeof entry.expression !== "object") entry.expression = {};
    entry.expression[which] = value;
    saveConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table
            columns={["animationName"]}
            data={keys.map(k => ({ animationName: k }))}
            selectedIndex={selectedKey ? keys.indexOf(selectedKey) : null}
            onSelect={(i) => setSelectedKey(keys[i])}
          />
        </div>

        <div style={{ width: 120, display: "flex", flexDirection: "column", gap: 6 }}>
          <button onClick={addAnimationGroup}>+</button>
          <button onClick={removeAnimationGroup} disabled={!selectedKey}>-</button>
        </div>
      </div>

      {selectedKey && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Animation: {selectedKey}</h3>
          <button onClick={addEntry}>+ entry</button>

          <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 8 }}>
            <thead>
              <tr>
                <th style={{ width: 90 }}>Trigger</th>
                <th style={{ width: 120 }}>Attribute</th>
                <th style={{ width: 120 }}>Quality (unknown)</th>
                <th style={{ width: 420 }}>Expr / Values</th>
                <th style={{ width: 120 }}>Default</th>
                <th style={{ width: 110 }}>Revert After (s)</th>
                <th style={{ width: 50 }}></th>
              </tr>
            </thead>
            <tbody>
              {(animations[selectedKey] || []).map((entry, idx) => {
                const mode = expressionModes[idx] || (typeof entry.expression === "object" ? "mapping" : "eval");
                return (
                  <tr key={idx}>
                    <td style={{ width: 90, padding: "0 8px" }}>
                      <select
                        value={entry.trigger_type || "datapoint"}
                        onChange={e => updateEntryField(idx, "trigger_type", e.target.value)}
                        style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                      >
                        <option value="datapoint">Datapoint</option>
                        <option value="alarm">Alarm</option>
                        <option value="connection">Communication</option>
                      </select>
                    </td>
                    <td style={{ width: 120, padding: "0 8px" }}>
                      <input
                        value={entry.attribute || ""}
                        onChange={e => updateEntryField(idx, "attribute", e.target.value)}
                        style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                      />
                    </td>
                    <td style={{ width: 120, padding: "0 8px" }}>
                      <input
                        value={entry.quality?.unknown || ""}
                        onChange={e => updateEntryField(idx, "quality", e.target.value)}
                        style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                      />
                    </td>
                    <td style={{ width: 420, padding: "0 8px" }}>
                      {/* Expr / Values cell */}
                      {entry.trigger_type === "alarm" ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                          {["ACTIVE", "INACTIVE", "FINISHED", "ACK"].map(f => (
                            <div key={f}>
                              <label style={{ fontSize: 12, color: "#333" }}>{f}:</label><br />
                              <input
                                style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                                value={(entry.expression && entry.expression[f]) || ""}
                                onChange={e => updateAlarmExpression(idx, f, e.target.value)}
                                placeholder={`value for ${f}`}
                              />
                            </div>
                          ))}
                        </div>
                      ) : entry.trigger_type === "connection" ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                          {["ONLINE", "OFFLINE"].map(f => (
                            <div key={f}>
                              <label style={{ fontSize: 12, color: "#333" }}>{f}:</label><br />
                              <input
                                style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                                value={(entry.expression && entry.expression[f]) || ""}
                                onChange={e => updateAlarmExpression(idx, f, e.target.value)}
                                placeholder={`value for ${f}`}
                              />
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                          <select
                            value={mode}
                            onChange={e => setExpressionModes(prev => ({ ...prev, [idx]: e.target.value }))}
                            style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                          >
                            <option value="eval">Eval Expression</option>
                            <option value="mapping">Mapping Expression</option>
                          </select>
                          {mode === "eval" ? (
                            <textarea
                              rows={2}
                              style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                              value={typeof entry.expression === "string" ? entry.expression : ""}
                              onChange={e => updateEntryField(idx, "expression", e.target.value)}
                            />
                          ) : (
                            <MappingEditor
                              value={typeof entry.expression === "object" ? entry.expression : {}}
                              onChange={val => updateEntryField(idx, "expression", JSON.stringify(val))}
                            />
                          )}
                        </div>
                      )}
                    </td>
                    <td style={{ width: 120, padding: "0 8px" }}>
                      <input
                        value={entry.default || ""}
                        onChange={e => updateEntryField(idx, "default", e.target.value)}
                        placeholder="default"
                        style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                      />
                    </td>
                    <td style={{ width: 110, padding: "0 8px" }}>
                      <input
                        type="number"
                        min="0"
                        step="0.1"
                        value={entry.revert_after || ""}
                        onChange={e => updateEntryField(idx, "revert_after", e.target.value)}
                        style={{ width: "80px", boxSizing: "border-box", padding: "2px 6px" }}
                      />
                    </td>
                    <td style={{ width: 50, padding: "0 8px" }}>
                      <button onClick={() => removeEntry(idx)}>Del</button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/* MappingEditor kept for non-alarm/mapping expressions */
function MappingEditor({ value, onChange }) {
  const [mapData, setMapData] = useState(Object.entries(value || {}));

  useEffect(() => {
    setMapData(Object.entries(value || {}));
  }, [value]);

  function updateKeyValue(idx, key, val) {
    const copy = [...mapData];
    copy[idx] = [key, val];
    setMapData(copy);
    onChange(Object.fromEntries(copy));
  }

  function addRow() {
    const copy = [...mapData, ["", ""]];
    setMapData(copy);
    onChange(Object.fromEntries(copy));
  }

  function removeRow(idx) {
    const copy = [...mapData];
    copy.splice(idx, 1);
    setMapData(Object.fromEntries(copy));
  }

  return (
    <div>
      {mapData.map(([k, v], i) => (
        <div key={i} style={{ display: "flex", gap: 6, marginBottom: 4 }}>
          <input value={k} onChange={e => updateKeyValue(i, e.target.value, v)} placeholder="key" />
          <input value={v} onChange={e => updateKeyValue(i, k, e.target.value)} placeholder="value" />
          <button onClick={() => removeRow(i)}>Del</button>
        </div>
      ))}
      <button onClick={addRow}>+ mapping</button>
    </div>
  );
}
