import React, { useState, useEffect } from "react";
import Table from "./Table";

export default function DriversTab({ config, setConfig }) {
  const [selected, setSelected] = useState(null);
  const drivers = config.drivers || [];
  const dpTypes = Object.keys(config.dp_types || {});
  const [newDp, setNewDp] = useState({ name: '', type: '', kind: '' });

  useEffect(() => {
    if (selected != null && selected >= drivers.length) setSelected(null);
  }, [drivers.length, selected]);

  function addDriver() {
    const name = prompt('Driver name:');
    if (!name) return;
    const cls = prompt('Driver class:');
    const copy = JSON.parse(JSON.stringify(config));
    copy.drivers.push({ name, driver_class: cls || '', connection_info: { server_name: '' }, datapoints: [], command_datapoints: [] });
    setConfig(copy);
    setSelected(copy.drivers.length - 1);
  }

  function removeDriver() {
    if (selected == null) return;
    if (!window.confirm('Delete selected driver?')) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.drivers.splice(selected, 1);
    setConfig(copy);
    setSelected(null);
  }

  function updateField(field, value) {
    const copy = JSON.parse(JSON.stringify(config));
    copy.drivers[selected][field] = value;
    setConfig(copy);
  }

  function startAddingDp(kind) {
    setNewDp({ name: '', type: dpTypes[0] || '', kind });
  }

  function confirmAddDp() {
    if (!newDp.name || !newDp.type) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.drivers[selected][newDp.kind].push({ name: newDp.name, type: newDp.type });
    setConfig(copy);
    setNewDp({ name: '', type: '', kind: '' });
  }

  function removeDatapoint(kind, idx) {
    if (!window.confirm('Delete datapoint?')) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.drivers[selected][kind].splice(idx, 1);
    setConfig(copy);
  }

  function updateConnectionInfo(key, value) {
    const copy = JSON.parse(JSON.stringify(config));
    if (!copy.drivers[selected].connection_info) copy.drivers[selected].connection_info = {};
    copy.drivers[selected].connection_info[key] = value;
    setConfig(copy);
  }

  function removeConnectionKey(key) {
    if (key === 'server_name') return; // always required
    const copy = JSON.parse(JSON.stringify(config));
    delete copy.drivers[selected].connection_info[key];
    setConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table
            columns={["name", "driver_class"]}
            data={drivers}
            selectedIndex={selected}
            onSelect={setSelected}
          />
        </div>
        <div style={{ width: 120, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <button onClick={addDriver}>+</button>
          <button onClick={removeDriver}>-</button>
        </div>
      </div>

      {selected != null && drivers[selected] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Driver</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
            <label>Name:</label>
            <input value={drivers[selected].name || ''} onChange={e => updateField('name', e.target.value)} />

            <label>Driver Class:</label>
            <input value={drivers[selected].driver_class || ''} onChange={e => updateField('driver_class', e.target.value)} />

            <label>Connection Info:</label>
            <div style={{ border: '1px solid #ccc', padding: 6, borderRadius: 4 }}>
              {Object.entries(drivers[selected].connection_info || {}).map(([k, v]) => (
                <div key={k} style={{ display: 'flex', gap: 4, marginBottom: 4, alignItems: 'center' }}>
                  <input style={{ flex: 1 }} value={k} disabled={k === 'server_name'} />
                  <input style={{ flex: 2 }} value={v} onChange={e => updateConnectionInfo(k, e.target.value)} />
                  {k !== 'server_name' && <button onClick={() => removeConnectionKey(k)}>Del</button>}
                </div>
              ))}
              <button onClick={() => {
                const key = prompt('Key:');
                if (!key || key === 'server_name') return;
                const value = prompt('Value:');
                updateConnectionInfo(key, value);
              }}>+ param</button>
            </div>
          </div>

          <div style={{ marginTop: 12 }}>
            <h4>Datapoints</h4>
            <button onClick={() => startAddingDp('datapoints')}>+ dp</button>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 8 }}>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {drivers[selected].datapoints.map((dp, idx) => (
                  <tr key={idx}>
                    <td>{dp.name}</td>
                    <td>{dp.type}</td>
                    <td><button onClick={() => removeDatapoint('datapoints', idx)}>Del</button></td>
                  </tr>
                ))}
                {newDp.kind === 'datapoints' && (
                  <tr>
                    <td>
                      <input value={newDp.name} onChange={e => setNewDp({...newDp, name: e.target.value})} />
                    </td>
                    <td>
                      <select value={newDp.type} onChange={e => setNewDp({...newDp, type: e.target.value})}>
                        {dpTypes.map(dt => <option key={dt} value={dt}>{dt}</option>)}
                      </select>
                    </td>
                    <td>
                      <button onClick={confirmAddDp}>Add</button>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>

            <h4>Command Datapoints</h4>
            <button onClick={() => startAddingDp('command_datapoints')}>+ cmd</button>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 8 }}>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {drivers[selected].command_datapoints.map((dp, idx) => (
                  <tr key={idx}>
                    <td>{dp.name}</td>
                    <td>{dp.type}</td>
                    <td><button onClick={() => removeDatapoint('command_datapoints', idx)}>Del</button></td>
                  </tr>
                ))}
                {newDp.kind === 'command_datapoints' && (
                  <tr>
                    <td>
                      <input value={newDp.name} onChange={e => setNewDp({...newDp, name: e.target.value})} />
                    </td>
                    <td>
                      <select value={newDp.type} onChange={e => setNewDp({...newDp, type: e.target.value})}>
                        {dpTypes.map(dt => <option key={dt} value={dt}>{dt}</option>)}
                      </select>
                    </td>
                    <td>
                      <button onClick={confirmAddDp}>Add</button>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
