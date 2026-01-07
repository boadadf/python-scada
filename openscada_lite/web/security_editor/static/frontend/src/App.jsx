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
 *   GET  /security/api/config      - loads the current security_config.json
 *   POST /security/api/config      - saves the edited security_config.json
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
import "./App.css";
import TopMenu from "./components/TopMenu";
import Tabs from "./components/Tabs";
import UsersTab from "./components/UsersTab";
import GroupsTab from "./components/GroupsTab";

// Shared login package
import { AuthProvider, useAuth, Login } from "login";

const DEFAULT_CONFIG = { users: [], groups: [] };

// Always use this constant for backend operations
const CONFIG_FILENAME = "system_config.json";

function SecureApp() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [activeTab, setActiveTab] = useState("Users");
  const [dirty, setDirty] = useState(false);

  async function loadConfig(signal) {
    try {
      const res = await fetch("/security/api/config", { signal });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setConfig(data);
      setDirty(false);
    } catch (err) {
      if (err.name === "AbortError" || err.name === "TypeError") return;
      alert("Failed to load config: " + err.message);
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    loadConfig(controller.signal);
    return () => controller.abort();
  }, []);

  async function saveConfig() {
    try {
      const res = await fetch("/security/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      if (!res.ok) throw new Error(await res.text());
      alert("Saved");
      setDirty(false);
    } catch (err) {
      alert("Failed to save: " + err.message);
    }
  }

  return (
    <div style={{ fontFamily: "Arial, sans-serif", height: "100vh", display: "flex", flexDirection: "column" }}>
      <TopMenu onLoad={loadConfig} onSave={saveConfig} dirty={dirty} />

      <div style={{ padding: 8 }}>
        <Tabs tabs={["Users", "Groups"]} active={activeTab} onChange={setActiveTab} />
        <div style={{ border: "1px solid #ddd", padding: 8, background: "#fff", flex: 1, overflow: "auto" }}>
          {activeTab === "Users" && (
            <UsersTab config={config} setConfig={(c) => { setConfig(c); setDirty(true); }} />
          )}
          {activeTab === "Groups" && (
            <GroupsTab 
              config={config} 
              setConfig={(c) => { setConfig(c); setDirty(true); }}
              activeTab={activeTab}
            />
          )}
        </div>
      </div>

      <div style={{ padding: 8, borderTop: "1px solid #ddd", background: "#fafafa" }}>
        <span>{dirty ? "* Unsaved changes" : "All changes saved"}</span>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <RequireAuth>
        <SecureApp />
      </RequireAuth>
    </AuthProvider>
  );
}

// ------------------------------
// Auth Wrapper (fixed)
// ------------------------------
function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return null;

  if (!isAuthenticated) {
    return <Login redirectPath="/security-editor/" />;
  }

  return children;
}
