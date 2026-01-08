import React, { useState } from "react";
import { useAuth } from "./AuthContext";
import { Api } from "generatedApi";
import "./login.css";

const api = new Api({
  baseUrl: "",
  credentials: "include",
});

const APP_LINKS = [
  { href: "/scada", label: "SCADA" },
  { href: "/security-editor", label: "Security Config" },
  { href: "/config-editor", label: "System Config" },
];

function getOtherApps(currentPath) {
  if (currentPath.startsWith("/scada"))
    return APP_LINKS.filter(l => l.href !== "/scada");
  if (currentPath.startsWith("/security-editor"))
    return APP_LINKS.filter(l => l.href !== "/security-editor");
  if (currentPath.startsWith("/config-editor"))
    return APP_LINKS.filter(l => l.href !== "/config-editor");
  return APP_LINKS;
}

function getSubtitle(currentPath) {
  if (currentPath.startsWith("/scada")) return "SCADA App";
  if (currentPath.startsWith("/security-editor")) return "Security configuration App";
  if (currentPath.startsWith("/config-editor")) return "System configuration App";
  return "OpenSCADA Lite";
}

function getAppName(currentPath) {
  if (currentPath.startsWith("/scada")) return "scada";
  if (currentPath.startsWith("/security-editor")) return "security_editor";
  if (currentPath.startsWith("/config-editor")) return "config_editor";
  return "unknown";
}

export default function Login({
  onLoginSuccess,
  redirectPath = "/",
}) {
  const { login } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const currentPath = window.location.pathname;
  const otherApps = getOtherApps(currentPath);
  const subtitle = getSubtitle(currentPath);
  const appName = getAppName(currentPath);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await api.security.login(
        { username, password },
        { app: appName }
      );

      console.debug("Login response:", res);

      // ✅ unwrap swagger-typescript-api response
      const payload = res.data;

      if (!payload || payload.status !== "ok") {
        throw new Error(payload?.reason || "Login failed");
      }

      // Set in-memory auth state; cookie is already set by backend
      login(payload.user);

      // Avoid full page reload; let RequireAuth render the app
      if (onLoginSuccess) {
        onLoginSuccess();
      }
    } catch (err) {
      console.error("Login error:", err);
      setError("Invalid credentials");
    } finally {
      setLoading(false);
    }
  }


  return (
    <div className="osl-login-bg">
      {/* App switch links */}
      <div
        style={{
          position: "fixed",
          top: 18,
          right: 32,
          zIndex: 100,
          display: "flex",
          gap: 18,
          fontSize: 15,
          fontWeight: 500,
        }}
      >
        {otherApps.map(link => (
          <a
            key={link.href}
            href={link.href}
            style={{
              color: "#333",
              textDecoration: "none",
              padding: "2px 10px",
              borderRadius: 4,
              background: "rgba(33,33,33,0.07)",
            }}
          >
            {link.label}
          </a>
        ))}
      </div>

      <div className="osl-login-box">
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

        {/* Test hint */}
        <div
          style={{
            marginTop: 18,
            color: "red",
            textAlign: "center",
            fontSize: 14,
            fontWeight: 500,
          }}
        >
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
