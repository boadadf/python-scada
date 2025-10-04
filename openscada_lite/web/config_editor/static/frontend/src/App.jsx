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
import "./App.css";
import { AuthProvider, useAuth, Login } from "login";
import TopMenu from "./components/TopMenu";
import Tabs from "./components/Tabs";
import ModulesTab from "./components/ModulesTab";
import DatapointTypesTab from "./components/DatapointTypesTab";
import DriversTab from "./components/DriversTab";
import RulesTab from "./components/RulesTab";

const DEFAULT_CONFIG = {
  modules: [],
  dp_types: {},
  drivers: [],
  rules: []
};

export default function App() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [activeTab, setActiveTab] = useState('Modules');
  const [dirty, setDirty] = useState(false);

  useEffect(() => { loadConfig(); }, []);


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
    if (!window.confirm("Saving will cause a restart in the SCADA application. Do you want to continue?")) {
      return;
    }
    try {
      const res = await fetch('/config-editor/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      if (!res.ok) throw new Error(await res.text());
      alert('Saved. The application will now restart.');
      await fetch('/config-editor/api/restart', { method: 'POST' });
      // Optionally, show a "restarting" message or reload the page after a delay
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
              <div className={activeTab === 'Modules' ? 'tab-content active' : 'tab-content'}>
                <ModulesTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />
              </div>
              <div className={activeTab === 'Datapoint Types' ? 'tab-content active' : 'tab-content'}>
                <DatapointTypesTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />
              </div>
              <div className={activeTab === 'Drivers' ? 'tab-content active' : 'tab-content'}>
                <DriversTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />
              </div>
              <div className={activeTab === 'Rules' ? 'tab-content active' : 'tab-content'}>
                <RulesTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />
              </div>
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