import React, { useState, useEffect } from "react";
import Table from "./Table";

export default function GroupsTab({ config, setConfig }) {
  const [selected, setSelected] = useState(null);
  const groups = config.groups || [];

  useEffect(() => {
    if (selected != null && selected >= groups.length) setSelected(null);
  }, [groups.length]);

  function add() {
    const name = prompt('Group name:');
    if (!name) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.groups.push({ name, permissions: [] });
    setConfig(copy);
    setSelected(copy.groups.length - 1);
  }

  function remove() {
    if (selected == null) return; if (!window.confirm('Delete selected group?')) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.groups.splice(selected, 1);
    setConfig(copy);
    setSelected(null);
  }

  function updateField(field, value) {
    const copy = JSON.parse(JSON.stringify(config));
    copy.groups[selected][field] = value;
    setConfig(copy);
  }

  function updatePermissions(permsArr) {
    const copy = JSON.parse(JSON.stringify(config));
    copy.groups[selected].permissions = permsArr;
    setConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table columns={['name', 'permissions']} data={groups.map(g => ({ ...g, permissions: (g.permissions || []).join(', ') }))} selectedIndex={selected} onSelect={setSelected} />
        </div>
        <div style={{ width: 120, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <button onClick={add}>+</button>
          <button onClick={remove}>-</button>
        </div>
      </div>
      {selected != null && groups[selected] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Group</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
            <label>Name:</label>
            <input value={groups[selected].name} onChange={e => updateField('name', e.target.value)} />
            <label>Permissions (comma separated):</label>
            <input value={(groups[selected].permissions || []).join(', ')} onChange={e => updatePermissions(e.target.value.split(',').map(s => s.trim()).filter(Boolean))} />
          </div>
        </div>
      )}
    </div>
  );
}