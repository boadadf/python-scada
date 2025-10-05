import React, { useState, useEffect } from "react";
import Table from "./Table";

export default function AnimationTab({ config, setConfig }) {
  const [selectedKey, setSelectedKey] = useState(null);
  const [editingIndex, setEditingIndex] = useState(null);
  const [expressionModes, setExpressionModes] = useState({}); // mode per entry
  const animations = config.animations || {};
  const keys = Object.keys(animations);

  // Initialize expression modes for existing entries
  useEffect(() => {
    if (!selectedKey) return;
    const newModes = {};
    (animations[selectedKey] || []).forEach((entry, idx) => {
      newModes[idx] = typeof entry.expression === 'object' ? 'mapping' : 'eval';
    });
    setExpressionModes(newModes);
  }, [selectedKey, animations]);

  function addAnimationGroup() {
    const name = prompt("New animation name:");
    if (!name) return;
    const copy = structuredClone(config);
    if (!copy.animations) copy.animations = {};
    copy.animations[name] = [];
    setConfig(copy);
    setSelectedKey(name);
  }

  function removeAnimationGroup() {
    if (!selectedKey) return;
    if (!window.confirm("Delete selected animation group?")) return;
    const copy = structuredClone(config);
    delete copy.animations[selectedKey];
    setConfig(copy);
    setSelectedKey(null);
  }

  function addEntry() {
    if (!selectedKey) return;
    const copy = structuredClone(config);
    copy.animations[selectedKey].push({ attribute: "", quality: { unknown: "" }, expression: "" });
    setConfig(copy);
    setEditingIndex(copy.animations[selectedKey].length - 1);
    setExpressionModes(prev => ({ ...prev, [copy.animations[selectedKey].length - 1]: 'eval' }));
  }

  function removeEntry(idx) {
    if (!selectedKey) return;
    const copy = structuredClone(config);
    copy.animations[selectedKey].splice(idx, 1);
    setConfig(copy);
    setExpressionModes(prev => {
      const newModes = { ...prev };
      delete newModes[idx];
      return newModes;
    });
  }

  function updateEntry(idx, field, value) {
    const copy = structuredClone(config);
    const mode = expressionModes[idx];
    if (field === "quality") {
      copy.animations[selectedKey][idx].quality.unknown = value;
    } else if (field === "expression") {
      if (mode === "mapping") {
        try {
          copy.animations[selectedKey][idx][field] = JSON.parse(value);
        } catch {
          copy.animations[selectedKey][idx][field] = {};
        }
      } else {
        copy.animations[selectedKey][idx][field] = value;
      }
    } else {
      copy.animations[selectedKey][idx][field] = value;
    }
    setConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table
            columns={["animationName"]}
            data={keys.map((k) => ({ animationName: k }))}
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
                <th>Attribute</th>
                <th>Quality (unknown)</th>
                <th>Expression (Eval or Mapping)</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
                {(animations[selectedKey] || []).map((entry, idx) => {
                    const mode = expressionModes[idx] || (typeof entry.expression === 'object' ? 'mapping' : 'eval');

                    return (
                    <tr key={idx}>
                      <td>
                        <input value={entry.attribute || ''} onChange={e => updateEntry(idx, 'attribute', e.target.value)} />
                      </td>
                      <td>
                        <input value={entry.quality?.unknown || ''} onChange={e => updateEntry(idx, 'quality', e.target.value)} />
                      </td>
                      <td>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          <select value={mode} onChange={e => setExpressionModes(prev => ({ ...prev, [idx]: e.target.value }))}>
                            <option value="eval">Eval Expression</option>
                            <option value="mapping">Mapping Expression</option>
                          </select>
                          {mode === 'eval' ? (
                            <textarea
                                rows={2}
                                style={{ width: '100%' }}
                                value={typeof entry.expression === 'string' ? entry.expression : ''}
                                onChange={e => updateEntry(idx, 'expression', e.target.value)}
                            />
                          ) : (
                            <MappingEditor
                                value={typeof entry.expression === 'object' ? entry.expression : {}}
                                onChange={val => updateEntry(idx, 'expression', JSON.stringify(val))}
                            />
                          )}
                        </div>
                      </td>
                      <td>
                        {mode === 'eval' && (
                          <button onClick={() => removeEntry(idx)}>Del</button>
                        )}
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

function MappingEditor({ value, onChange }) {
  const [mapData, setMapData] = useState(Object.entries(value));

  useEffect(() => {
    setMapData(Object.entries(value));
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
      {mapData.map(([k, v], idx) => (
        <div key={idx} style={{ display: 'flex', gap: 4, marginBottom: 2 }}>
          <input value={k} onChange={e => updateKeyValue(idx, e.target.value, v)} placeholder="key" />
          <input value={v} onChange={e => updateKeyValue(idx, k, e.target.value)} placeholder="value" />
          <button onClick={() => removeRow(idx)}>Del</button>
        </div>
      ))}
      <button onClick={addRow}>+ mapping</button>
    </div>
  );
}