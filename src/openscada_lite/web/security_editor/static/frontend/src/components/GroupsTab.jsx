import React, { useState, useEffect, useMemo } from "react";
import Table from "./Table";
import { Api } from "generatedApi";

export default function GroupsTab({ config, setConfig, activeTab }) {
  const [selected, setSelected] = useState(null);
  const [endpoints, setEndpoints] = useState([]);
  const groups = config.groups || [];

  const api = useMemo(() => new Api(), []);

  // Fetch endpoints via OpenAPI client
  useEffect(() => {
    async function fetchEndpoints() {
      try {
        const token = localStorage.getItem("jwt_token");
        const res = await api.security.getRegisteredEndpoints({
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        setEndpoints(Array.isArray(res.data) ? res.data : []);
      } catch (err) {
        console.error("Error fetching endpoints:", err);
        setEndpoints([]);
      }
    }
    fetchEndpoints();
  }, [api]);

  useEffect(() => {
    if (selected != null && selected >= groups.length) setSelected(null);
  }, [groups.length, selected]);

  function add() {
    const name = prompt("Group name:");
    if (!name) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.groups.push({ name, permissions: [] });
    setConfig(copy);
    setSelected(copy.groups.length - 1);
  }

  function remove() {
    if (selected == null) return;
    if (!window.confirm("Delete selected group?")) return;
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
      <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table
            columns={["name", "permissions"]}
            data={groups.map(g => ({
              ...g,
              permissions: (g.permissions || []).join(", "),
            }))}
            selectedIndex={selected}
            onSelect={setSelected}
          />
        </div>
        <div style={{ width: 120, display: "flex", flexDirection: "column", gap: 6 }}>
          <button onClick={add}>+</button>
          <button onClick={remove}>-</button>
        </div>
      </div>

      {selected != null && groups[selected] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Group</h3>

          <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", gap: 8 }}>
            <label>Name:</label>
            <input
              value={groups[selected].name}
              onChange={e => updateField("name", e.target.value)}
            />
          </div>

          <h4>Allowed Endpoints</h4>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left" }}>Endpoint</th>
                <th style={{ textAlign: "center" }}>Allowed</th>
              </tr>
            </thead>
            <tbody>
              {endpoints.map(endpoint => (
                <tr key={endpoint}>
                  <td>{endpoint}</td>
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
