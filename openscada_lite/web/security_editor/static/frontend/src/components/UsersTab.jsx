import React, { useState, useEffect } from "react";
import Table from "./Table";
import { sha256 } from "js-sha256";

const ALL_APPS = [
  { value: "scada", label: "SCADA" },
  { value: "security_editor", label: "Security Editor" },
  { value: "config_editor", label: "System Config Editor" }
];

export default function UsersTab({ config, setConfig }) {
  const [selected, setSelected] = useState(null);
  const [passwordInput, setPasswordInput] = useState(""); // local state for password

  const users = config.users || [];
  const groups = config.groups || [];

  useEffect(() => {
    setPasswordInput(""); // clear password input when changing user
  }, [selected]);

  function add() {
    const username = prompt('Username:');
    if (!username) return;
    const password = prompt('Password:');
    if (!password) return;
    const password_hash = sha256(password);
    const copy = JSON.parse(JSON.stringify(config));
    copy.users.push({ username, password_hash, groups: [], allowed_apps: [] });
    setConfig(copy);
    setSelected(copy.users.length - 1);
  }

  function remove() {
    if (selected == null) return;
    if (!window.confirm('Delete selected user?')) return;
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

  function toggleAllowedApp(appValue) {
    const copy = JSON.parse(JSON.stringify(config));
    const allowed = copy.users[selected].allowed_apps || [];
    if (allowed.includes(appValue)) {
      copy.users[selected].allowed_apps = allowed.filter(a => a !== appValue);
    } else {
      copy.users[selected].allowed_apps = [...allowed, appValue];
    }
    setConfig(copy);
  }

  function setSingleGroup(groupName) {
    const copy = JSON.parse(JSON.stringify(config));
    copy.users[selected].groups = [groupName];
    setConfig(copy);
  }

  function setPassword() {
    if (!passwordInput) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.users[selected].password_hash = sha256(passwordInput);
    setConfig(copy);
    setPasswordInput(""); // clear after setting
    alert("Password updated!");
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
            <label>Change Password:</label>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                type="password"
                value={passwordInput}
                onChange={e => setPasswordInput(e.target.value)}
                placeholder="New password"
              />
              <button type="button" onClick={setPassword}>Set</button>
            </div>
            <label>Group:</label>
            <table style={{ width: "100%", background: "#fafaff", borderCollapse: "collapse" }}>
              <tbody>
                {groups.map(g => (
                  <tr key={g.name}>
                    <td>
                      <input
                        type="radio"
                        name="user-group"
                        checked={users[selected].groups && users[selected].groups[0] === g.name}
                        onChange={() => setSingleGroup(g.name)}
                      />
                    </td>
                    <td>{g.name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <label>Allowed Apps:</label>
            <table style={{ width: "100%", background: "#fafaff", borderCollapse: "collapse" }}>
              <tbody>
                {ALL_APPS.map(app => (
                  <tr key={app.value}>
                    <td>
                      <input
                        type="checkbox"
                        checked={users[selected].allowed_apps && users[selected].allowed_apps.includes(app.value)}
                        onChange={() => toggleAllowedApp(app.value)}
                      />
                    </td>
                    <td>{app.label}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}