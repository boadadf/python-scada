import React, { useState, useEffect } from "react";
import Table from "./Table";

/**
 * AnimationTab.jsx
 *
 * - triggerType: "datapoint" | "alarm"
 * - if triggerType === "alarm":
 *     - show alarmEvent selector
 *     - force "Alarm Expression" editor: two fields ACTIVE / INACTIVE
 * - otherwise allow Eval or Mapping expressions
 *
 * Expression for alarm entries is stored as an object:
 *   { "ACTIVE": "<value-for-active>", "INACTIVE": "<value-for-inactive>" }
 */

export default function AnimationTab({ config, setConfig }) {
  const [selectedKey, setSelectedKey] = useState(null);
  const [expressionModes, setExpressionModes] = useState({}); // 'eval' | 'mapping' | 'alarm'
  const animations = config.animations || {};
  const keys = Object.keys(animations);

  // Initialize expression modes whenever a group is selected
  useEffect(() => {
    if (!selectedKey) return;
    const newModes = {};
    (animations[selectedKey] || []).forEach((entry, idx) => {
      if (entry.triggerType === "alarm") {
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
      triggerType: "datapoint",
      alarmEvent: "",          // used only when triggerType === 'alarm'
      attribute: "",
      quality: { unknown: "" },
      expression: "",          // string or object or alarm-mapping object
      duration: 0.5,
      default: "",             // explicit revert target
      revertAfter: 0
    };
    copy.animations[selectedKey].push(newEntry);
    saveConfig(copy);
    // set expression mode for the new entry
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
    // normalize numeric fields
    if (field === "duration" || field === "revertAfter") {
      entry[field] = rawValue === "" ? 0 : Number(rawValue);
    } else if (field === "quality") {
      if (!entry.quality) entry.quality = {};
      entry.quality.unknown = rawValue;
    } else if (field === "triggerType") {
      entry.triggerType = rawValue;
      // if switched to alarm, force expression mode to 'alarm' and ensure structure
      if (rawValue === "alarm") {
        setExpressionModes(prev => ({ ...prev, [idx]: "alarm" }));
        // initialize alarm expression mapping when missing
        if (!entry.expression || typeof entry.expression !== "object" || !("ACTIVE" in entry.expression)) {
          entry.expression = { ACTIVE: "", INACTIVE: "" };
        }
        if (!entry.alarmEvent) entry.alarmEvent = "onAlarmActive";
      } else {
        // switch to non-alarm: set default mode if needed
        setExpressionModes(prev => ({ ...prev, [idx]: typeof entry.expression === "object" ? "mapping" : "eval" }));
      }
    } else if (field === "expression") {
      const mode = expressionModes[idx];
      if (mode === "mapping") {
        // user provides JSON string (rare) — try parse
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
                <th style={{ width: 120 }}>Trigger</th>
                <th style={{ width: 140 }}>Alarm Event</th>
                <th>Attribute</th>
                <th>Quality (unknown)</th>
                <th>Expr / Alarm values</th>
                <th>Default</th>
                <th style={{ width: 110 }}>Revert After (s)</th>
                <th style={{ width: 70 }}></th>
              </tr>
            </thead>
            <tbody>
              {(animations[selectedKey] || []).map((entry, idx) => {
                const mode = expressionModes[idx] || (entry.triggerType === "alarm" ? "alarm" : (typeof entry.expression === "object" ? "mapping" : "eval"));
                return (
                  <tr key={idx}>
                    <td style={{ width: 120, padding: "0 8px" }}>
                      <select
                        value={entry.triggerType || "datapoint"}
                        onChange={e => updateEntryField(idx, "triggerType", e.target.value)}
                        style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                      >
                        <option value="datapoint">Datapoint</option>
                        <option value="alarm">Alarm</option>
                      </select>
                    </td>
                    <td style={{ width: 140, padding: "0 8px" }}>
                      {entry.triggerType === "alarm" ? (
                        <select
                          value={entry.alarmEvent || "onAlarmActive"}
                          onChange={e => updateEntryField(idx, "alarmEvent", e.target.value)}
                          style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                        >
                          <option value="onAlarmActive">onAlarmActive</option>
                          <option value="onAlarmAck">onAlarmAck</option>
                          <option value="onAlarmInactive">onAlarmInactive</option>
                          <option value="onAlarmFinished">onAlarmFinished</option>
                        </select>
                      ) : (
                        <span style={{ opacity: 0.5 }}>—</span>
                      )}
                    </td>
                    <td style={{ padding: "0 8px" }}>
                      <input
                        value={entry.attribute || ""}
                        onChange={e => updateEntryField(idx, "attribute", e.target.value)}
                        style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                      />
                    </td>
                    <td style={{ padding: "0 8px" }}>
                      <input
                        value={entry.quality?.unknown || ""}
                        onChange={e => updateEntryField(idx, "quality", e.target.value)}
                        style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                      />
                    </td>
                    <td style={{ padding: "0 8px" }}>
                      {/* Expression area */}
                      {entry.triggerType === "alarm" ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                          <div>
                            <label style={{ fontSize: 12, color: "#333" }}>When {entry.alarmEvent || "onAlarmActive"} is TRUE (ACTIVE):</label><br />
                            <input
                              style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                              value={(entry.expression && entry.expression.ACTIVE) || ""}
                              onChange={e => updateAlarmExpression(idx, "ACTIVE", e.target.value)}
                              placeholder="value when ACTIVE"
                            />
                          </div>
                          <div>
                            <label style={{ fontSize: 12, color: "#333" }}>When FALSE (INACTIVE):</label><br />
                            <input
                              style={{ width: "100%", boxSizing: "border-box", padding: "2px 6px" }}
                              value={(entry.expression && entry.expression.INACTIVE) || ""}
                              onChange={e => updateAlarmExpression(idx, "INACTIVE", e.target.value)}
                              placeholder="value when INACTIVE"
                            />
                          </div>
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
                    <td style={{ padding: "0 8px" }}>
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
                        value={entry.revertAfter || ""}
                        onChange={e => updateEntryField(idx, "revertAfter", e.target.value)}
                        style={{ width: "80px", boxSizing: "border-box", padding: "2px 6px" }}
                      />
                    </td>
                    <td style={{ width: 70, padding: "0 8px" }}>
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

/* MappingEditor kept for non-alarm mapping expressions */
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
    setMapData(copy);
    onChange(Object.fromEntries(copy));
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
