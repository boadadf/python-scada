import React from "react";
import { useAuth } from "login";
import { useUserAction } from "../contexts/UserActionContext"; // <-- import
import { usePing } from "../contexts/PingContext";

export default function StatusBar() {
  const { payload } = useUserAction(); // <-- get payload
  const { isConnected } = usePing();

  return (
    <div className="status-bar" style={{ display: "flex", alignItems: "center", gap: "0.5em" }}>
      <div className="status-bar-item" style={{ flex: 1, textAlign: "left" }}>
        <span className="status-bar-label">Last action:</span>
        {payload ? (
          <span style={{ fontSize: "0.85em", marginLeft: "0.5em" }}>
            User: <b>{payload.user}</b>,&nbsp;
            Endpoint: <b>{payload.endpoint}</b>,&nbsp;
            Status: <b>{payload.status}</b>,&nbsp;
            Timestamp: <b>{payload.timestamp}</b>
          </span>
        ) : (
          <span style={{ fontSize: "0.85em" }}>No user action</span>
        )}
      </div>
      <span className="status-bar-separator" style={{ margin: "0 0.5em" }}>|</span>
      <div className="status-bar-item">
        <span className="status-bar-label">Connection:</span>
        <span
          className={
            "status-bar-icon " +
            (isConnected ? "status-bar-icon-online" : "status-bar-icon-offline")
          }
        ></span>
      </div>
    </div>
  );
}