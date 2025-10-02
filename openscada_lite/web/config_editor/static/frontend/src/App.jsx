/*
SCADA Config Editor React App
Drop this file into: openscada_lite/web/config_editor/static/frontend/src/App.jsx

Build with your existing webpack setup (entry ./src/index.jsx imports App.jsx)

Features implemented:
- Top menu File: New, Load, Save, Upload
- Tabs: Modules, Datapoint Types, Drivers, Rules
- Each tab: top table with items, +/- buttons to add/delete
- Selecting a row shows a detail form below for editing
- Save button sends POST /config-editor/api/config
- Load uses GET /config-editor/api/config
- Upload calls POST /config-editor/api/reload

This is a single-file React implementation using fetch (no external libs).
Keep index.jsx as entry that mounts this App.
*/

import React, { useEffect, useState } from 'react';

const DEFAULT_CONFIG = {
  modules: [
    { name: 'alarm' },
    { name: 'command' },
    { name: 'communication' },
    { name: 'datapoint' },
    { name: 'animation' },
    { name: 'tracking', config: { p1: 'file', p2: 'flow_events.log' } }
  ],
  dp_types: {
    LEVEL: { type: 'float', min: 0, max: 100, default: 0.0 },
    OPENED_CLOSED: { type: 'enum', values: ['OPENED', 'CLOSED'], default: 'CLOSED' },
    OPEN_CLOSE_CMD: { type: 'enum', values: ['OPEN', 'CLOSE', 'TOGGLE'], default: 'CLOSE' },
    START_STOP: { type: 'enum', values: ['STARTED', 'STOPPED'], default: 'STOPPED' },
    START_STOP_CMD: { type: 'enum', values: ['START', 'STOP', 'TOGGLE'], default: 'STOP' },
    PRESSURE: { type: 'float', min: 0, max: 200, default: 50.0 },
    TEMPERATURE: { type: 'float', min: 100, max: 150, default: 120.0 }
  },
  drivers: [
    {
      name: 'Server1',
      driver_class: 'TankTestDriver',
      connection_info: { server_name: 'Server1' },
      datapoints: [
        { name: 'TANK', type: 'LEVEL' },
        { name: 'PUMP', type: 'OPENED_CLOSED' },
        { name: 'DOOR', type: 'OPENED_CLOSED' },
        { name: 'TEST', type: 'START_STOP' }
      ],
      command_datapoints: [
        { name: 'PUMP_CMD', type: 'OPEN_CLOSE_CMD' },
        { name: 'DOOR_CMD', type: 'OPEN_CLOSE_CMD' },
        { name: 'TEST_CMD', type: 'START_STOP_CMD' }
      ]
    },
    {
      name: 'Server2',
      driver_class: 'BoilerTestDriver',
      connection_info: { server_name: 'Server2' },
      datapoints: [
        { name: 'VALVE', type: 'OPENED_CLOSED' },
        { name: 'PRESSURE', type: 'PRESSURE' },
        { name: 'TEMPERATURE', type: 'TEMPERATURE' },
        { name: 'HEATER', type: 'OPENED_CLOSED' },
        { name: 'TEST', type: 'START_STOP' }
      ],
      command_datapoints: [
        { name: 'VALVE_CMD', type: 'OPENED_CLOSED_CMD' },
        { name: 'HEATER_CMD', type: 'OPEN_CLOSE_CMD' },
        { name: 'TEST_CMD', type: 'START_STOP_CMD' }
      ]
    }
  ],
  rules: [
    {
      rule_id: 'close_valve_if_high',
      on_condition: "Server2@PRESSURE > 100",
      on_actions: ["send_command('Server2@VALVE', 0)", 'raise_alarm()'],
      off_condition: 'Server2@PRESSURE < 80',
      off_actions: ['lower_alarm()']
    },
    {
      rule_id: 'pump_start_if_low_level',
      on_condition: "float(Server1@TANK) < 10",
      on_actions: ["send_command('Server1@PUMP_CMD', 'OPEN')", "send_command('Server1@DOOR_CMD', 'CLOSE')", 'raise_alarm()']
    },
    { rule_id: 'door_open_alarm', on_condition: 'Server1@DOOR == OPENED', on_actions: ['raise_alarm()'] },
    { rule_id: 'temperature_high_warning', on_condition: 'Server2@TEMPERATURE > 80', on_actions: ['raise_alarm()'] }
  ]
};

function TopMenu({ onNew, onLoad, onSave, onUpload }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', borderBottom: '1px solid #ddd', background: '#f7f7f7' }}>
      <div style={{ fontWeight: 'bold' }}>SCADA Config Editor</div>
      <div>
        <button onClick={onNew}>New</button>
        <button onClick={onLoad}>Load</button>
        <button onClick={onSave}>Save</button>
        <button onClick={onUpload}>Upload</button>
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

function ModulesTab({ config, setConfig }) {
  const [selected, setSelected] = useState(null);
  const modules = config.modules || [];

  useEffect(() => {
    if (selected != null && selected >= modules.length) setSelected(null);
  }, [modules.length]);

  function add() {
    const name = prompt('Module name:');
    if (!name) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.modules.push({ name });
    setConfig(copy);
    setSelected(copy.modules.length - 1);
  }

  function remove() {
    if (selected == null) return; if (!confirm('Delete selected module?')) return;
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
          <Table columns={[ 'name' ]} data={modules} selectedIndex={selected} onSelect={setSelected} />
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
            <input value={modules[selected].name || ''} onChange={e => updateField('name', e.target.value)} />
            <label>Config (JSON):</label>
            <textarea value={JSON.stringify(modules[selected].config || {}, null, 2)} onChange={e => {
              try { updateField('config', JSON.parse(e.target.value)); } catch (ex) { /* ignore invalid */ }
            }} rows={6} />
          </div>
        </div>
      )}
    </div>
  );
}

function DpTypesTab({ config, setConfig }) {
  const [selected, setSelected] = useState(null);
  const keys = Object.keys(config.dp_types || {});

  useEffect(() => {
    if (selected != null && selected >= keys.length) setSelected(null);
  }, [keys.length]);

  function add() {
    const name = prompt('New datapoint type name (e.g. MY_TYPE):');
    if (!name) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.dp_types[name] = { type: 'float', min: 0, max: 100, default: 0 };
    setConfig(copy);
    setSelected(keys.length);
  }

  function remove() {
    if (selected == null) return; if (!confirm('Delete selected dp_type?')) return;
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
          <Table columns={[ 'typeName', 'type', 'default' ]} data={keys.map(k => ({ typeName: k, ...config.dp_types[k] }))} selectedIndex={selected} onSelect={setSelected} />
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
            <select value={config.dp_types[keys[selected]].type} onChange={e => updateField('type', e.target.value)}>
              <option value="float">float</option>
              <option value="enum">enum</option>
              <option value="int">int</option>
              <option value="string">string</option>
            </select>
            <label>Values (csv for enum):</label>
            <input value={(config.dp_types[keys[selected]].values || []).join(', ')} onChange={e => updateField('values', e.target.value)} />
            <label>Min:</label>
            <input value={config.dp_types[keys[selected]].min ?? ''} onChange={e => updateField('min', e.target.value)} />
            <label>Max:</label>
            <input value={config.dp_types[keys[selected]].max ?? ''} onChange={e => updateField('max', e.target.value)} />
            <label>Default:</label>
            <input value={String(config.dp_types[keys[selected]].default ?? '')} onChange={e => updateField('default', e.target.value)} />
          </div>
        </div>
      )}
    </div>
  );
}

function DriversTab({ config, setConfig }) {
  const [selected, setSelected] = useState(null);
  const drivers = config.drivers || [];

  useEffect(() => {
    if (selected != null && selected >= drivers.length) setSelected(null);
  }, [drivers.length]);

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
    if (selected == null) return; if (!confirm('Delete selected driver?')) return;
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
    if (!confirm('Delete datapoint?')) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.drivers[selected][kind].splice(idx, 1);
    setConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table columns={[ 'name', 'driver_class' ]} data={drivers} selectedIndex={selected} onSelect={setSelected} />
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
            <input value={drivers[selected].name || ''} onChange={e => updateField('name', e.target.value)} />
            <label>Driver Class:</label>
            <input value={drivers[selected].driver_class || ''} onChange={e => updateField('driver_class', e.target.value)} />
            <label>Connection Info (JSON):</label>
            <textarea value={JSON.stringify(drivers[selected].connection_info || {}, null, 2)} onChange={e => {
              try { updateField('connection_info', JSON.parse(e.target.value)); } catch (ex) {}
            }} rows={4} />
          </div>

          <div style={{ marginTop: 12 }}>
            <h4>Datapoints</h4>
            <button onClick={() => addDatapoint('datapoints')}>+ dp</button>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 8 }}>
              <thead><tr><th>Name</th><th>Type</th><th></th></tr></thead>
              <tbody>
                {(drivers[selected].datapoints || []).map((dp, idx) => (
                  <tr key={idx}><td>{dp.name}</td><td>{dp.type}</td><td><button onClick={() => removeDatapoint('datapoints', idx)}>Del</button></td></tr>
                ))}
              </tbody>
            </table>

            <h4>Command Datapoints</h4>
            <button onClick={() => addDatapoint('command_datapoints')}>+ cmd</button>
            <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 8 }}>
              <thead><tr><th>Name</th><th>Type</th><th></th></tr></thead>
              <tbody>
                {(drivers[selected].command_datapoints || []).map((dp, idx) => (
                  <tr key={idx}><td>{dp.name}</td><td>{dp.type}</td><td><button onClick={() => removeDatapoint('command_datapoints', idx)}>Del</button></td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function RulesTab({ config, setConfig }) {
  const [selected, setSelected] = useState(null);
  const rules = config.rules || [];

  useEffect(() => {
    if (selected != null && selected >= rules.length) setSelected(null);
  }, [rules.length]);

  function add() {
    const id = prompt('Rule id:');
    if (!id) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.rules.push({ rule_id: id, on_condition: '', on_actions: [], off_condition: '', off_actions: [] });
    setConfig(copy);
    setSelected(copy.rules.length - 1);
  }

  function remove() {
    if (selected == null) return; if (!confirm('Delete selected rule?')) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.rules.splice(selected, 1);
    setConfig(copy);
    setSelected(null);
  }

  function updateField(field, value) {
    const copy = JSON.parse(JSON.stringify(config));
    copy.rules[selected][field] = value;
    setConfig(copy);
  }

  function addAction(kind) {
    const act = prompt('Action (javascript-like string):');
    if (!act) return;
    const copy = JSON.parse(JSON.stringify(config));
    copy.rules[selected][kind].push(act);
    setConfig(copy);
  }

  function removeAction(kind, idx) {
    const copy = JSON.parse(JSON.stringify(config));
    copy.rules[selected][kind].splice(idx, 1);
    setConfig(copy);
  }

  return (
    <div style={{ padding: 12 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <Table columns={[ 'rule_id', 'on_condition' ]} data={rules} selectedIndex={selected} onSelect={setSelected} />
        </div>
        <div style={{ width: 120, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <button onClick={add}>+</button>
          <button onClick={remove}>-</button>
        </div>
      </div>

      {selected != null && rules[selected] && (
        <div style={{ marginTop: 12 }}>
          <h3>Edit Rule</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: 8 }}>
            <label>Rule ID:</label>
            <input value={rules[selected].rule_id} onChange={e => updateField('rule_id', e.target.value)} />
            <label>On condition:</label>
            <input value={rules[selected].on_condition} onChange={e => updateField('on_condition', e.target.value)} />
            <label>On actions:</label>
            <div>
              <button onClick={() => addAction('on_actions')}>+ action</button>
              <ul>
                {(rules[selected].on_actions || []).map((a, i) => (
                  <li key={i}>{a} <button onClick={() => removeAction('on_actions', i)}>Del</button></li>
                ))}
              </ul>
            </div>
            <label>Off condition:</label>
            <input value={rules[selected].off_condition || ''} onChange={e => updateField('off_condition', e.target.value)} />
            <label>Off actions:</label>
            <div>
              <button onClick={() => addAction('off_actions')}>+ action</button>
              <ul>
                {(rules[selected].off_actions || []).map((a, i) => (
                  <li key={i}>{a} <button onClick={() => removeAction('off_actions', i)}>Del</button></li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [activeTab, setActiveTab] = useState('Modules');
  const [dirty, setDirty] = useState(false);

  useEffect(() => { setDirty(false); }, []);

  function newConfig() {
    if (!confirm('Discard current and create new?')) return;
    setConfig(JSON.parse(JSON.stringify(DEFAULT_CONFIG)));
    setDirty(true);
  }

  async function loadConfig() {
    try {
      const res = await fetch('/config-editor/api/config');
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
      const res = await fetch('/config-editor/api/config', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(config) });
      if (!res.ok) throw new Error(await res.text());
      alert('Saved');
      setDirty(false);
    } catch (err) {
      alert('Failed to save: ' + err.message);
    }
  }

  async function uploadConfig() {
    try {
      const res = await fetch('/config-editor/api/reload', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'unknown');
      alert('Upload: ' + data.message);
    } catch (err) {
      alert('Failed to upload: ' + err.message);
    }
  }

  return (
    <div style={{ fontFamily: 'Arial, sans-serif', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <TopMenu onNew={newConfig} onLoad={loadConfig} onSave={saveConfig} onUpload={uploadConfig} />
      <div style={{ padding: 8 }}>
        <Tabs tabs={[ 'Modules', 'Datapoint Types', 'Drivers', 'Rules' ]} active={activeTab} onChange={setActiveTab} />
        <div style={{ border: '1px solid #ddd', padding: 8, background: '#fff', flex: 1, overflow: 'auto' }}>
          {activeTab === 'Modules' && <ModulesTab config={config} setConfig={(c)=>{setConfig(c); setDirty(true);}} />}
          {activeTab === 'Datapoint Types' && <DpTypesTab config={config} setConfig={(c)=>{setConfig(c); setDirty(true);}} />}
          {activeTab === 'Drivers' && <DriversTab config={config} setConfig={(c)=>{setConfig(c); setDirty(true);}} />}
          {activeTab === 'Rules' && <RulesTab config={config} setConfig={(c)=>{setConfig(c); setDirty(true);}} />}
        </div>
      </div>
      <div style={{ padding: 8, borderTop: '1px solid #ddd', background: '#fafafa' }}>
        <span>{dirty ? '* Unsaved changes' : 'All changes saved'}</span>
      </div>
    </div>
  );
}
