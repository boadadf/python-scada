import React, { useState, useEffect } from "react";
import Table from "./Table";

export default function DriversTab({ config, setConfig }) {
  const [selected, setSelected] = useState(null);
  const drivers = config.drivers || [];

  useEffect(() => {
    if (selected != null && selected >= drivers.length) setSelected(null);
  }, [drivers.length, selected]);

  function add() {
    const name = prompt('Driver name:');
    if (!name) return;
    const cls = prompt('Driver class:');
    const copy = JSON.parse(JSON.stringify(config));
    copy.drivers.push({ name, driver_class: cls || '', connection_info: {}, datapoints: [], command_datapoints: [] });
    setConfig(copy);
    setSelected(copy.drivers.length - 1);
  }

  function remove() {
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

  function addDatapoint(kind) {
    const name = prompt('Datapoint name:');
    const type = prompt('Datapoint type (e.g. LEVEL):');
    if (!name || !type) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.drivers[selected][kind].push({ name, type });
    setConfig(copy);
  }

  function removeDatapoint(kind, idx) {
    if (!window.confirm('Delete datapoint?')) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.drivers[selected][kind].splice(idx, 1);
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
          <button onClick={add}>+</button>
          <button onClick={remove}>-</button>
        </div>
      </div>

      {selected != null && drivers[selected] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Driver</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
            <label>Name:</label>
            <input
              value={drivers[selected].name || ''}
              onChange={e => updateField('name', e.target.value)}
            />
            <label>Driver Class:</label>
            <input
              value={drivers[selected].driver_class || ''}
              onChange={e => updateField('driver_class', e.target.value)}
            />
            <label>Connection Info (JSON):</label>
            <textarea
              value={JSON.stringify(drivers[selected].connection_info || {}, null, 2)}
              onChange={e => {
                try {
                  updateField('connection_info', JSON.parse(e.target.value));
                } catch (ex) {}
              }}
              rows={4}
            />
          </div>

          <div style={{ marginTop: 12 }}>
            <h4>Datapoints</h4>
            <button onClick={() => addDatapoint('datapoints')}>+ dp</button>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 8 }}>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {(drivers[selected].datapoints || []).map((dp, idx) => (
                  <tr key={idx}>
                    <td>{dp.name}</td>
                    <td>{dp.type}</td>
                    <td>
                      <button onClick={() => removeDatapoint('datapoints', idx)}>Del</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h4>Command Datapoints</h4>
            <button onClick={() => addDatapoint('command_datapoints')}>+ cmd</button>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 8 }}>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {(drivers[selected].command_datapoints || []).map((dp, idx) => (
                  <tr key={idx}>
                    <td>{dp.name}</td>
                    <td>{dp.type}</td>
                    <td>
                      <button onClick={() => removeDatapoint('command_datapoints', idx)}>Del</button>
                    </td>
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