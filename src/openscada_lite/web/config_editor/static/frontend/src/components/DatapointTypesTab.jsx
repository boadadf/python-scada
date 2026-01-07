import React, { useState, useEffect } from "react";
import Table from "./Table";

export default function DatapointTypesTab({ config, setConfig }) {
  const [selectedKey, setSelectedKey] = useState(null);
  const keys = Object.keys(config.dp_types || {});

  useEffect(() => {
    if (selectedKey && !keys.includes(selectedKey)) {
      setSelectedKey(null);
    }
  }, [keys, selectedKey]);

  function add() {
    const name = prompt("New datapoint type name (e.g. MY_TYPE):");
    if (!name) return;

    const copy = structuredClone(config);
    if (!copy.dp_types) copy.dp_types = {};
    copy.dp_types[name] = { type: "float", min: 0, max: 100, default: 0 };
    setConfig(copy);
    setSelectedKey(name);
  }

  function remove() {
    if (!selectedKey) return;
    if (!window.confirm("Delete selected dp_type?")) return;

    const copy = structuredClone(config);
    delete copy.dp_types[selectedKey];
    setConfig(copy);
    setSelectedKey(null);
  }

  function updateField(field, value) {
    if (!selectedKey) return;
    const copy = structuredClone(config);
    const dpType = copy.dp_types[selectedKey];

    if (dpType.type === "enum") {
      if (field === "default") {
        // Force default to be one of the enum values
        if ((dpType.values || []).includes(value)) {
          dpType.default = value;
        }
      } else if (field === "min" || field === "max") {
        // Disable min/max for enums
        return;
      } else if (field === "values") {
        dpType.values = value.split(",").map(s => s.trim()).filter(s => s.length);
        if (!dpType.values.includes(dpType.default)) {
          dpType.default = dpType.values[0] || '';
        }
      } else {
        dpType[field] = value;
      }
    } else {
      if (field === "values") {
        dpType[field] = value.split(",").map(s => s.trim()).filter(s => s.length);
      } else if (field === "min" || field === "max" || field === "default") {
        const num = Number(value);
        dpType[field] = isNaN(num) ? value : num;
      } else {
        dpType[field] = value;
      }
    }

    setConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table
            columns={["typeName", "type", "default"]}
            data={keys.map(k => ({ typeName: k, ...config.dp_types[k] }))}
            selectedIndex={selectedKey ? keys.indexOf(selectedKey) : null}
            onSelect={i => setSelectedKey(keys[i])}
          />
        </div>
        <div style={{ width: 120, display: "flex", flexDirection: "column", gap: 6 }}>
          <button onClick={add}>+</button>
          <button onClick={remove} disabled={!selectedKey}>-</button>
        </div>
      </div>

      {selectedKey && config.dp_types[selectedKey] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Datapoint Type: {selectedKey}</h3>
          <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 8 }}>
            <label>Type:</label>
            <select
              value={config.dp_types[selectedKey].type}
              onChange={e => updateField("type", e.target.value)}
            >
              <option value="float">float</option>
              <option value="int">int</option>
              <option value="string">string</option>
              <option value="enum">enum</option>
            </select>

            {config.dp_types[selectedKey].type === "enum" ? (
              <>
                <label>Enum Values:</label>
                <div>
                  <button onClick={() => {
                    const val = prompt("Add enum value:");
                    if (val) {
                      const copy = structuredClone(config);
                      if (!copy.dp_types[selectedKey].values) copy.dp_types[selectedKey].values = [];
                      copy.dp_types[selectedKey].values.push(val);
                      if (!copy.dp_types[selectedKey].default) copy.dp_types[selectedKey].default = val;
                      setConfig(copy);
                    }
                  }}>+ value</button>
                  <ul>
                    {(config.dp_types[selectedKey].values || []).map((v, i) => (
                      <li key={i}>{v} <button onClick={() => {
                        const copy = structuredClone(config);
                        copy.dp_types[selectedKey].values.splice(i, 1);
                        if (!copy.dp_types[selectedKey].values.includes(copy.dp_types[selectedKey].default)) {
                          copy.dp_types[selectedKey].default = copy.dp_types[selectedKey].values[0] || '';
                        }
                        setConfig(copy);
                      }}>Del</button></li>
                    ))}
                  </ul>
                </div>

                <label>Default:</label>
                <select
                  value={config.dp_types[selectedKey].default}
                  onChange={e => updateField("default", e.target.value)}
                >
                  {(config.dp_types[selectedKey].values || []).map((v, i) => (
                    <option key={i} value={v}>{v}</option>
                  ))}
                </select>
              </>
            ) : (
              <>
                <label>Min:</label>
                <input
                  value={config.dp_types[selectedKey].min ?? ''}
                  onChange={e => updateField("min", e.target.value)}
                />
                <label>Max:</label>
                <input
                  value={config.dp_types[selectedKey].max ?? ''}
                  onChange={e => updateField("max", e.target.value)}
                />
                <label>Default:</label>
                <input
                  value={String(config.dp_types[selectedKey].default ?? '')}
                  onChange={e => updateField("default", e.target.value)}
                />
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
