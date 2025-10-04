import React, { useState } from "react";
import { useAuth } from "./AuthContext";
import "./login.css";

export default function Login({ onLoginSuccess, loginEndpoint = "/security/login", redirectPath = "/" }) {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch(loginEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      if (!res.ok) throw new Error("Login failed");
      const data = await res.json();
      login(data.token, data.user);
      setLoading(false);
      if (onLoginSuccess) onLoginSuccess();
      else window.location.href = redirectPath;
    } catch (err) {
      setError("Invalid credentials");
      setLoading(false);
    }
  }

  return (
    <div className="osl-login-bg">
      <form className="osl-login-form" onSubmit={handleSubmit}>
        <div className="osl-login-title">OSL</div>
        <div className="osl-login-subtitle">Open Scada Lite</div>
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
    </div>
  );
}