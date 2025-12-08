import React, { useState } from "react";
import { useAuth } from "./AuthContext";
import "./login.css";

const APP_LINKS = [
  { href: "/scada", label: "SCADA" },
  { href: "/security-editor", label: "Security Config" },
  { href: "/config-editor", label: "System Config" }
];

function getOtherApps(currentPath) {
  if (currentPath.startsWith("/scada")) {
    return APP_LINKS.filter(link => link.href !== "/scada");
  }
  if (currentPath.startsWith("/security-editor")) {
    return APP_LINKS.filter(link => link.href !== "/security-editor");
  }
  if (currentPath.startsWith("/config-editor")) {
    return APP_LINKS.filter(link => link.href !== "/config-editor");
  }
  // Default: show all
  return APP_LINKS;
}

function getSubtitle(currentPath) {
  if (currentPath.startsWith("/scada")) return "SCADA App";
  if (currentPath.startsWith("/security-editor")) return "Security configuration App";
  if (currentPath.startsWith("/config-editor")) return "System configuration App";
  return "Open Scada Lite";
}

export default function Login({ onLoginSuccess, loginEndpoint = "/security/login", redirectPath = "/" }) {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const otherApps = getOtherApps(window.location.pathname);
  const subtitle = getSubtitle(window.location.pathname);

  function getAppName(currentPath) {
    if (currentPath.startsWith("/scada")) return "scada";
    if (currentPath.startsWith("/security-editor")) return "security_editor";
    if (currentPath.startsWith("/config-editor")) return "config_editor";
    return "unknown";
  }

  const appName = getAppName(window.location.pathname);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(`${loginEndpoint}?app=${appName}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      if (!res.ok) throw new Error("Login failed");
      const result = await res.json();
      if (result.status === "ok") {
        login(result.data.token, result.data.user);
        setLoading(false);
        if (onLoginSuccess) onLoginSuccess();
        else window.location.href = redirectPath;
      } else {
        setError(result.reason || "Login failed");
        setLoading(false);
      }
    } catch (err) {
      setError("Invalid credentials");
      setLoading(false);
    }
  }

  return (
    <div className="osl-login-bg">
      {/* App links at the most top-right of the page */}
      <div style={{
        position: "fixed",
        top: 18,
        right: 32,
        zIndex: 100,
        display: "flex",
        gap: 18,
        fontSize: 15,
        fontWeight: 500
      }}>
        {otherApps.map(link => (
          <a
            key={link.href}
            href={link.href}
            style={{
              color: "#333",
              textDecoration: "none",
              padding: "2px 10px",
              borderRadius: 4,
              transition: "background 0.2s",
              background: "rgba(33,33,33,0.07)"
            }}
            onMouseOver={e => e.currentTarget.style.background = "#eee"}
            onMouseOut={e => e.currentTarget.style.background = "rgba(33,33,33,0.07)"}
          >
            {link.label}
          </a>
        ))}
      </div>
      <div className="osl-login-box" style={{ position: "relative" }}>
        <form className="osl-login-form" onSubmit={handleSubmit}>
          <div className="osl-login-title">OSL</div>
          <div className="osl-login-subtitle">{subtitle}</div>
          {error && <div className="osl-login-error">{error}</div>}
          <input
            type="text"
            placeholder="Username"
            autoFocus
            value={username}
            onChange={e => setUsername(e.target.value)}
            className="osl-login-input"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="osl-login-input"
          />
          <button
            type="submit"
            disabled={loading}
            className="osl-login-btn"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
         {/* Dani: Added test-system hint - remove for prod*/}
        <div style={{
          marginTop: "18px",
          color: "red",
          textAlign: "center",
          fontSize: "14px",
          fontWeight: "500"
        }}>
          Hint:<br />
          This is a test system, login with <b>admin / admin</b><br />
          Or create your own user at{" "}
          <a
            href={`${window.location.origin}/security-editor/`}
            style={{ color: "red", textDecoration: "underline" }}
          >
            OSL Security Editor
          </a>
        </div>
      </div>
    </div>
  );
}