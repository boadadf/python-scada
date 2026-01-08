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

import React, { useEffect, useState, lazy, Suspense, useMemo } from 'react';
import "./App.css";
import { AuthProvider, useAuth, Login } from "login";
import TopMenu from "./components/TopMenu";
import Tabs from "./components/Tabs";
import ModulesTab from "./components/ModulesTab";
import DatapointTypesTab from "./components/DatapointTypesTab";
import DriversTab from "./components/DriversTab";
import RulesTab from "./components/RulesTab";
import AnimationsTab from "./components/AnimationsTab";
import GisIconsTab from "./components/GisIconsTab";
import StreamsTab from "./components/StreamsTab";
import FrontendTab from "./components/FrontendTab";
import { Api, ContentType } from "generatedApi";

// Lazy-load AnimationTestTab
const AnimationTestTab = lazy(() => import("./components/AnimationTestTab"));

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
  const [currentConfigName, setCurrentConfigName] = useState("system_config");

  // OpenAPI client instance
  const api = useMemo(() => new Api(), []);

  // Dialog state
  const [showLoadDialog, setShowLoadDialog] = useState(false);
  const [showSaveAsDialog, setShowSaveAsDialog] = useState(false);
  const [availableConfigs, setAvailableConfigs] = useState([]);
  const [selectedConfig, setSelectedConfig] = useState("");
  const [saveAsFilename, setSaveAsFilename] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Use AuthProvider to check authentication
  function RequireAuth({ children }) {
    const { isAuthenticated } = useAuth();
    useEffect(() => {
      setIsAuthenticated(isAuthenticated);
    }, [isAuthenticated]);
    if (!isAuthenticated) {
      return <Login redirectPath="/config-editor" />;
    }
    return children;
  }

  // Show load dialog after login
  useEffect(() => {
    if (isAuthenticated) {
      openLoadDialog();
    }
    // eslint-disable-next-line
  }, [isAuthenticated]);

  async function loadConfigByName(name) {
    try {
      const res = await api.configEditor.getConfigByName(name);
      const data = res?.data;
      setConfig(data);
      setCurrentConfigName(name); // Track loaded config name
      setDirty(false);
      setShowLoadDialog(false);
    } catch (err) {
      alert('Failed to load config: ' + err.message);
    }
  }

  async function openLoadDialog() {
    try {
      const res = await api.configEditor.getConfigs();
      let files = res?.data || [];
      // Ensure system_config is present and first
      if (!files.includes("system_config")) {
        files.unshift("system_config");
      } else {
        // Move to first position if not already
        files = ["system_config", ...files.filter(f => f !== "system_config")];
      }
      setAvailableConfigs(files);
      setSelectedConfig("system_config"); // Default selection
      setShowLoadDialog(true);
    } catch (err) {
      alert('Failed to list configs: ' + err.message);
    }
  }

  async function saveConfig() {
    if (!currentConfigName) {
      alert("No config loaded. Please load a config first.");
      return;
    }
    try {
      const res = await api.configEditor.saveConfigAs({
        body: { config, filename: currentConfigName },
        type: ContentType.Json,
        format: 'json'
      });
      const data = res?.data || {};
      alert('Saved: ' + data.filename);
      setDirty(false);
    } catch (err) {
      alert('Failed to save: ' + err.message);
    }
  }

  async function saveConfigAs() {
    if (!saveAsFilename) {
      alert("Please enter a filename.");
      return;
    }
    try {
      const res = await api.configEditor.saveConfigAs({
        body: { config, filename: saveAsFilename },
        type: ContentType.Json,
        format: 'json'
      });
      const data = res?.data || {};
      alert('Saved as: ' + data.filename);
      setShowSaveAsDialog(false);
    } catch (err) {
      alert('Failed to save as: ' + err.message);
    }
  }

  async function uploadConfig() {
    try {
      const res = await api.configEditor.saveConfigAs({
        body: { config, filename: "system_config.json" },
        type: ContentType.Json,
        format: 'json'
      });
      const data = res?.data || {};
      alert('Uploaded and restarting: ' + data.filename);
      await api.configEditor.restart();
      setTimeout(() => {
        window.location.reload();
      }, 3000);
    } catch (err) {
      alert('Failed to upload: ' + err.message);
    }
  }

  return (
    <AuthProvider>
      <RequireAuth>
        <div style={{ fontFamily: 'Arial, sans-serif', height: '100vh', display: 'flex', flexDirection: 'column' }}>
          <TopMenu
            onLoad={openLoadDialog}
            onSave={saveConfig}
            onSaveAs={() => setShowSaveAsDialog(true)}
            onUpload={uploadConfig}
            dirty={dirty}
          />
          {/* Load Dialog */}
          {showLoadDialog && (
            <div style={{
              position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
              background: 'rgba(0,0,0,0.2)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <div style={{ background: '#fff', padding: 24, borderRadius: 8, minWidth: 320 }}>
                <h3>Select Config to Load</h3>
                <select
                  style={{ width: '100%', marginBottom: 16 }}
                  value={selectedConfig}
                  onChange={e => setSelectedConfig(e.target.value)}
                >
                  <option value="">-- Select --</option>
                  {availableConfigs.map(f => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
                <button
                  disabled={!selectedConfig}
                  onClick={() => loadConfigByName(selectedConfig)}
                  style={{ marginRight: 8 }}
                >Load</button>
                <button onClick={() => setShowLoadDialog(false)}>Cancel</button>
              </div>
            </div>
          )}
          {/* Save As Dialog */}
          {showSaveAsDialog && (
            <div style={{
              position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
              background: 'rgba(0,0,0,0.2)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <div style={{ background: '#fff', padding: 24, borderRadius: 8, minWidth: 320 }}>
                <h3>Save As New Config</h3>
                <input
                  type="text"
                  style={{ width: '100%', marginBottom: 16 }}
                  placeholder="Filename (e.g. my_system_config.json)"
                  value={saveAsFilename}
                  onChange={e => setSaveAsFilename(e.target.value)}
                />
                <button
                  disabled={!saveAsFilename}
                  onClick={saveConfigAs}
                  style={{ marginRight: 8 }}
                >Save As</button>
                <button onClick={() => setShowSaveAsDialog(false)}>Cancel</button>
              </div>
            </div>
          )}
          <div style={{ padding: 8 }}>
            <Tabs
              tabs={[
                'Modules',
                'Datapoint Types',
                'Drivers',
                'Rules',
                'Animations',
                'GIS Icons',
                'Animation Test',
                'Streams',
                'Frontend' // <-- Add this line
              ]}
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
              <div className={activeTab === 'Animations' ? 'tab-content active' : 'tab-content'}>
                <AnimationsTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />
              </div>
              <div className={activeTab === 'GIS Icons' ? 'tab-content active' : 'tab-content'}>
                <GisIconsTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />
              </div>
              <div className={activeTab === 'Streams' ? 'tab-content active' : 'tab-content'}>
                <StreamsTab config={config} setConfig={(c) => { setConfig(c); setDirty(true); }} />
              </div>
              <div className={activeTab === 'Frontend' ? 'tab-content active' : 'tab-content'}>
                <FrontendTab config={config} setConfig={c => { setConfig(c); setDirty(true); }} />
              </div>
              {activeTab === 'Animation Test' && (
                <Suspense fallback={<div style={{padding: 40, textAlign: "center"}}>Loading Animation Test...</div>}>
                  <AnimationTestTab />
                </Suspense>
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