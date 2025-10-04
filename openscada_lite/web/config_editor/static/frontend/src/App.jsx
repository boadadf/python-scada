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
import { AuthProvider, useAuth, Login } from "login";
import TopMenu from "./components/TopMenu";
import Tabs from "./components/Tabs";
import ModulesTab from "./components/ModulesTab";
import DatapointTypesTab from "./components/DatapointTypesTab";
import DriversTab from "./components/DriversTab";
import RulesTab from "./components/RulesTab";

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

export default function App() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [activeTab, setActiveTab] = useState('Modules');
  const [dirty, setDirty] = useState(false);

  function newConfig() {
    if (!window.confirm('Discard current and create new?')) return;
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
      const res = await fetch('/config-editor/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
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
    <AuthProvider>
      <RequireAuth>
        <div style={{ fontFamily: 'Arial, sans-serif', height: '100vh', display: 'flex', flexDirection: 'column' }}>
          <TopMenu
            onNew={newConfig}
            onLoad={loadConfig}
            onSave={saveConfig}
            onUpload={uploadConfig}
          />
          <div style={{ padding: 8 }}>
            <Tabs
              tabs={['Modules', 'Datapoint Types', 'Drivers', 'Rules']}
              active={activeTab}
              onChange={setActiveTab}
            />
            <div style={{ border: '1px solid #ddd', padding: 8, background: '#fff', flex: 1, overflow: 'auto' }}>
              {activeTab === 'Modules' && (
                <ModulesTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />
              )}
              {activeTab === 'Datapoint Types' && (
                <DatapointTypesTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />
              )}
              {activeTab === 'Drivers' && (
                <DriversTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />
              )}
              {activeTab === 'Rules' && (
                <RulesTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />
              )}
            </div>
          </div>
          <div style={{ padding: 8, borderTop: '1px solid #ddd', background: '#fafafa' }}>
            <span>{dirty ? '* Unsaved changes' : 'All changes saved'}</span>
          </div>
        </div>
      </RequireAuth>
    </AuthProvider>
  );
}
// RequireAuth component
function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Login redirectPath="/config-editor" />;
  }
  return children;
}