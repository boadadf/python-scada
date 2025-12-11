import React, { useState, useEffect } from "react";
import Table from "./Table";

export default function GroupsTab({ config, setConfig, activeTab }) {
  const [selected, setSelected] = useState(null);
  const [endpoints, setEndpoints] = useState([]);
  const groups = config.groups || [];

  // Fetch endpoints on mount
  useEffect(() => {
    console.debug("useEffect for fetching endpoints triggered"); // Debugging log
    async function fetchEndpoints() {
      console.debug("Fetching endpoints...");
      try {
        const token = localStorage.getItem("jwt_token");
        const res = await fetch("/security/endpoints", {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        if (res.ok) {
          const data = await res.json();
          setEndpoints(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        console.error("Error fetching endpoints:", err);
        setEndpoints([]);
      }
    }
    fetchEndpoints();
  }, []);


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
    if (selected == null) return;
    if (!window.confirm('Delete selected group?')) return;
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

  function togglePermission(endpoint) {
    const copy = JSON.parse(JSON.stringify(config));
    const group = copy.groups[selected];
    if (!group.permissions) group.permissions = [];
    if (group.permissions.includes(endpoint)) {
      group.permissions = group.permissions.filter(e => e !== endpoint);
    } else {
      group.permissions.push(endpoint);
    }
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
          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8, marginBottom: 16 }}>
            <label>Name:</label>
            <input value={groups[selected].name} onChange={e => updateField('name', e.target.value)} />
          </div>
          <h4>Allowed Endpoints</h4>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Endpoint</th>
                <th style={{ textAlign: "center", borderBottom: "1px solid #ccc" }}>Allowed</th>
              </tr>
            </thead>
            <tbody>
              {endpoints.map(endpoint => (
                <tr key={endpoint}>
                  <td style={{ padding: "4px 8px" }}>{endpoint}</td>
                  <td style={{ textAlign: "center" }}>
                    <input
                      type="checkbox"
                      checked={groups[selected].permissions?.includes(endpoint)}
                      onChange={() => togglePermission(endpoint)}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}