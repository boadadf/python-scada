import React, { useState, useEffect } from "react";
import { useAuth } from "login";

export default function StatusBar() {
  const { user } = useAuth();
  const [isConnected, setIsConnected] = useState(true);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch("/scada/ping");
        setIsConnected(res.ok);
      } catch {
        setIsConnected(false);
      }
    }, 5000); // check every 5 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="status-bar">
      <div className="status-bar-item">
        <span className="status-bar-label">User:</span> {user?.username || "Unknown"}
      </div>
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