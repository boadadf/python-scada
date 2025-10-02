/**
 * Security Config Editor (React)
 * 
 * This React app provides a user-friendly interface for editing the `security_config.json` file
 * of OpenSCADA Lite. It allows you to manage users, groups, and permissions in a style and UX
 * similar to the main config editor.
 * 
 * Features:
 * - View, add, edit, and delete users and groups.
 * - Assign users to groups.
 * - Assign permissions to groups (comma-separated).
 * - Tabs for Users and Groups.
 * - "New", "Load", and "Save" buttons for config management.
 * - Unsaved changes indicator.
 * - All changes are kept in memory until you click "Save".
 * 
 * API Endpoints (expected by this app):
 *   GET  /security-editor/api/config      - loads the current security_config.json
 *   POST /security-editor/api/config      - saves the edited security_config.json
 * 
 * Usage:
 * - Place this file as `App.jsx` in your security editor React project.
 * - Use an `index.jsx` to mount `<App />` (see your config editor for an example).
 * - Adjust API endpoints as needed for your backend.
 * 
 * Styling:
 * - Uses inline styles for a clean, modern look.
 * - Table and form layouts match the config editor for consistency.
 * 
 * Author: [Your Name or Team]
 * Date: [YYYY-MM-DD]
 */

import React, { useEffect, useState } from "react";

const DEFAULT_CONFIG = {
  users: [],
  groups: []
};

function TopMenu({ onNew, onLoad, onSave }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', borderBottom: '1px solid #ddd', background: '#f7f7f7' }}>
      <div style={{ fontWeight: 'bold' }}>Security Config Editor</div>
      <div>
        <button onClick={onNew}>New</button>
        <button onClick={onLoad}>Load</button>
        <button onClick={onSave}>Save</button>
      </div>
    </div>
  );
}

function Tabs({ tabs, active, onChange }) {
  return (
    <div style={{ display: 'flex', borderBottom: '1px solid #ddd' }}>
      {tabs.map(t => (
        <div key={t} onClick={() => onChange(t)} style={{ padding: '10px 14px', cursor: 'pointer', background: active === t ? '#fff' : '#f0f0f0', borderTop: '1px solid #ddd', borderLeft: '1px solid #ddd', borderRight: '1px solid #ddd' }}>{t}</div>
      ))}
    </div>
  );
}

function Table({ columns, data, selectedIndex, onSelect }) {
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr>
          {columns.map(col => <th key={col} style={{ border: '1px solid #ccc', padding: '6px', textAlign: 'left' }}>{col}</th>)}
        </tr>
      </thead>
      <tbody>
        {data.map((row, idx) => (
          <tr key={idx} onClick={() => onSelect(idx)} style={{ background: selectedIndex === idx ? '#e6f7ff' : 'transparent', cursor: 'pointer' }}>
            {columns.map(c => (
              <td key={c} style={{ border: '1px solid #eee', padding: '6px' }}>{String(row[c] === undefined ? (row[c.toLowerCase()] ?? '') : row[c])}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function UsersTab({ config, setConfig }) {
  const [selected, setSelected] = useState(null);
  const users = config.users || [];
  const groups = config.groups || [];

  useEffect(() => {
    if (selected != null && selected >= users.length) setSelected(null);
  }, [users.length]);

  function add() {
    const username = prompt('Username:');
    if (!username) return;
    const password = prompt('Password:');
    if (!password) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.users.push({ username, password, groups: [] });
    setConfig(copy);
    setSelected(copy.users.length - 1);
  }

  function remove() {
    if (selected == null) return; if (!window.confirm('Delete selected user?')) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.users.splice(selected, 1);
    setConfig(copy);
    setSelected(null);
  }

  function updateField(field, value) {
    const copy = JSON.parse(JSON.stringify(config));
    copy.users[selected][field] = value;
    setConfig(copy);
  }

  function updateGroups(groupsArr) {
    const copy = JSON.parse(JSON.stringify(config));
    copy.users[selected].groups = groupsArr;
    setConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table columns={['username', 'groups']} data={users.map(u => ({ ...u, groups: (u.groups || []).join(', ') }))} selectedIndex={selected} onSelect={setSelected} />
        </div>
        <div style={{ width: 120, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <button onClick={add}>+</button>
          <button onClick={remove}>-</button>
        </div>
      </div>
      {selected != null && users[selected] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit User</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
            <label>Username:</label>
            <input value={users[selected].username} onChange={e => updateField('username', e.target.value)} />
            <label>Password:</label>
            <input type="password" value={users[selected].password} onChange={e => updateField('password', e.target.value)} />
            <label>Groups:</label>
            <select multiple value={users[selected].groups || []} onChange={e => {
              const opts = Array.from(e.target.selectedOptions).map(o => o.value);
              updateGroups(opts);
            }}>
              {groups.map(g => <option key={g.name} value={g.name}>{g.name}</option>)}
            </select>
          </div>
        </div>
      )}
    </div>
  );
}

function GroupsTab({ config, setConfig }) {
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

export default function App() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [activeTab, setActiveTab] = useState('Users');
  const [dirty, setDirty] = useState(false);

  useEffect(() => { loadConfig(); }, []);

  function newConfig() {
    if (!window.confirm('Discard current and create new?')) return;
    setConfig(JSON.parse(JSON.stringify(DEFAULT_CONFIG)));
    setDirty(true);
  }

  async function loadConfig() {
    try {
      const res = await fetch('/security-editor/api/config');
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setConfig(data);
      setDirty(false);
    } catch (err) {
      alert('Failed to load config: ' + err.message);
    }
  }

  async function saveConfig() {
    try {
      const res = await fetch('/security-editor/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(config) });
      if (!res.ok) throw new Error(await res.text());
      alert('Saved');
      setDirty(false);
    } catch (err) {
      alert('Failed to save: ' + err.message);
    }
  }

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TopMenu onNew={newConfig} onLoad={loadConfig} onSave={saveConfig} />
      <div style={{ padding: 8 }}>
        <Tabs tabs={['Users', 'Groups']} active={activeTab} onChange={setActiveTab} />
        <div style={{ border: '1px solid #ddd', padding: 8, background: '#fff', flex: 1, overflow: 'auto' }}>
          {activeTab === 'Users' && <UsersTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />}
          {activeTab === 'Groups' && <GroupsTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />}
        </div>
      </div>
      <div style={{ padding: 8, borderTop: '1px solid #ddd', background: '#fafafa' }}>
        <span>{dirty ? '* Unsaved changes' : 'All changes saved'}</span>
      </div>
    </div>
  );
}