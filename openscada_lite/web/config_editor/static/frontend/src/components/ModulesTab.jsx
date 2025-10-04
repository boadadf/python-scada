import React, { useState, useEffect } from "react";
import Table from "./Table";

export default function ModulesTab({ config, setConfig }) {
  const [selected, setSelected] = useState(null);
  const modules = config.modules || [];

  useEffect(() => {
    if (selected != null && selected >= modules.length) setSelected(null);
  }, [modules.length, selected]);

  function add() {
    const name = prompt('Module name:');
    if (!name) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.modules.push({ name });
    setConfig(copy);
    setSelected(copy.modules.length - 1);
  }

  function remove() {
    if (selected == null) return;
    if (!window.confirm('Delete selected module?')) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.modules.splice(selected, 1);
    setConfig(copy);
    setSelected(null);
  }

  function updateField(field, value) {
    const copy = JSON.parse(JSON.stringify(config));
    copy.modules[selected][field] = value;
    setConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table
            columns={["name"]}
            data={modules}
            selectedIndex={selected}
            onSelect={setSelected}
          />
        </div>
        <div style={{ width: 120, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <button onClick={add}>+</button>
          <button onClick={remove}>-</button>
        </div>
      </div>

      {selected != null && modules[selected] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Module</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
            <label>Name:</label>
            <input
              value={modules[selected].name || ''}
              onChange={e => updateField('name', e.target.value)}
            />
            <label>Config (JSON):</label>
            <textarea
              value={JSON.stringify(modules[selected].config || {}, null, 2)}
              onChange={e => {
                try {
                  updateField('config', JSON.parse(e.target.value));
                } catch (ex) {
                  // ignore invalid JSON
                }
              }}
              rows={6}
            />
          </div>
        </div>
      )}
    </div>
  );
}