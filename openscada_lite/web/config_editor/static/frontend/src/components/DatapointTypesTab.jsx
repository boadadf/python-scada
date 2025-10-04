import React, { useState, useEffect } from "react";
import Table from "./Table";

export default function DatapointTypesTab({ config, setConfig }) {
  const [selected, setSelected] = useState(null);
  const keys = Object.keys(config.dp_types || {});

  useEffect(() => {
    if (selected != null && selected >= keys.length) setSelected(null);
  }, [keys.length, selected]);

  function add() {
    const name = prompt('New datapoint type name (e.g. MY_TYPE):');
    if (!name) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.dp_types[name] = { type: 'float', min: 0, max: 100, default: 0 };
    setConfig(copy);
    setSelected(keys.length);
  }

  function remove() {
    if (selected == null) return;
    if (!window.confirm('Delete selected dp_type?')) return;
    const key = keys[selected];
    const copy = JSON.parse(JSON.stringify(config));
    delete copy.dp_types[key];
    setConfig(copy);
    setSelected(null);
  }

  function updateField(field, value) {
    const key = keys[selected];
    const copy = JSON.parse(JSON.stringify(config));
    if (field === 'values') {
      copy.dp_types[key][field] = value.split(',').map(s => s.trim()).filter(s => s.length);
    } else if (field === 'min' || field === 'max' || field === 'default') {
      const num = Number(value);
      copy.dp_types[key][field] = isNaN(num) ? value : num;
    } else {
      copy.dp_types[key][field] = value;
    }
    setConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table
            columns={["typeName", "type", "default"]}
            data={keys.map(k => ({ typeName: k, ...config.dp_types[k] }))}
            selectedIndex={selected}
            onSelect={setSelected}
          />
        </div>
        <div style={{ width: 120, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <button onClick={add}>+</button>
          <button onClick={remove}>-</button>
        </div>
      </div>

      {selected != null && keys[selected] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Datapoint Type: {keys[selected]}</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
            <label>Type:</label>
            <select
              value={config.dp_types[keys[selected]].type}
              onChange={e => updateField('type', e.target.value)}
            >
              <option value="float">float</option>
              <option value="enum">enum</option>
              <option value="int">int</option>
              <option value="string">string</option>
            </select>
            <label>Values (csv for enum):</label>
            <input
              value={(config.dp_types[keys[selected]].values || []).join(', ')}
              onChange={e => updateField('values', e.target.value)}
            />
            <label>Min:</label>
            <input
              value={config.dp_types[keys[selected]].min ?? ''}
              onChange={e => updateField('min', e.target.value)}
            />
            <label>Max:</label>
            <input
              value={config.dp_types[keys[selected]].max ?? ''}
              onChange={e => updateField('max', e.target.value)}
            />
            <label>Default:</label>
            <input
              value={String(config.dp_types[keys[selected]].default ?? '')}
              onChange={e => updateField('default', e.target.value)}
            />
          </div>
        </div>
      )}
    </div>
  );
}