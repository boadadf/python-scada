/**
 * Security Config Editor (React)
 *
 * Fully rewritten to use generatedApi consistently.
 * - No fetch()
 * - Correct swagger response handling
 * - Stable auth flow
 */

import React, { useEffect, useState } from "react";
import "./App.css";

import TopMenu from "./components/TopMenu";
import Tabs from "./components/Tabs";
import UsersTab from "./components/UsersTab";
import GroupsTab from "./components/GroupsTab";

import { AuthProvider, useAuth, Login } from "login";
import { Api } from "generatedApi";

const DEFAULT_CONFIG = { users: [], groups: [] };

function SecureApp() {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [activeTab, setActiveTab] = useState("Users");
  const [dirty, setDirty] = useState(false);
  const api = new Api();

  // -----------------------------
  // Load security config
  // -----------------------------
  async function loadConfig(signal) {
    try {
      const res = await api.security.getSecurityConfig({ signal });
      console.debug("Loaded security config:", res.data);

      setConfig(res.data);
      setDirty(false);
    } catch (err) {
      if (err?.name === "AbortError") return;
      console.error("Failed to load security config:", err);
      alert("Failed to load security configuration");
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    loadConfig(controller.signal);
    return () => controller.abort();
  }, []);

  // -----------------------------
  // Save security config
  // -----------------------------
  async function saveConfig() {
    try {
      await api.security.saveSecurityConfig(config);
      alert("Saved");
      setDirty(false);
    } catch (err) {
      console.error("Failed to save security config:", err);
      alert("Failed to save security configuration");
    }
  }

  return (
    <div
      style={{
        fontFamily: "Arial, sans-serif",
        height: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <TopMenu onLoad={loadConfig} onSave={saveConfig} dirty={dirty} />

      <div style={{ padding: 8, flex: 1, display: "flex", flexDirection: "column" }}>
        <Tabs tabs={["Users", "Groups"]} active={activeTab} onChange={setActiveTab} />

        <div
          style={{
            border: "1px solid #ddd",
            padding: 8,
            background: "#fff",
            flex: 1,
            overflow: "auto",
          }}
        >
          {activeTab === "Users" && (
            <UsersTab
              config={config}
              setConfig={(c) => {
                setConfig(c);
                setDirty(true);
              }}
            />
          )}

          {activeTab === "Groups" && (
            <GroupsTab
              config={config}
              setConfig={(c) => {
                setConfig(c);
                setDirty(true);
              }}
            />
          )}
        </div>
      </div>

      <div
        style={{
          padding: 8,
          borderTop: "1px solid #ddd",
          background: "#fafafa",
        }}
      >
        <span>{dirty ? "* Unsaved changes" : "All changes saved"}</span>
      </div>
    </div>
  );
}

// ---------------------------------
// Auth wrapper (correct + minimal)
// ---------------------------------
function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return null;

  if (!isAuthenticated) {
    return <Login redirectPath="/security-editor/" />;
  }

  return children;
}

// ---------------------------------
// App root
// ---------------------------------
export default function App() {
  return (
    <AuthProvider>
      <RequireAuth>
        <SecureApp />
      </RequireAuth>
    </AuthProvider>
  );
}
