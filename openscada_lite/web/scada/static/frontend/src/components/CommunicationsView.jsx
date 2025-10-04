import React, { useEffect, useState } from "react";
// Make sure to install socket.io-client: npm install socket.io-client
import { io } from "socket.io-client";

export default function CommunicationsView() {
  const [drivers, setDrivers] = useState([]);
  const [socket, setSocket] = useState(null);

  // Setup Socket.IO and live updates
  useEffect(() => {
    const s = io();
    setSocket(s);

    s.on("connect", () => {
      s.emit("communication_subscribe_live_feed");
    });

    s.on("communication_initial_state", data => {
      setDrivers(Array.isArray(data) ? data : []);
    });

    s.on("communication_driverconnectstatus", data => {
      if (data.driver_name && data.status) {
        setDrivers(prev => {
          const idx = prev.findIndex(d => d.driver_name === data.driver_name);
          if (idx !== -1) {
            // Update existing
            const updated = [...prev];
            updated[idx] = { ...updated[idx], status: data.status };
            return updated;
          } else {
            // Add new
            return [...prev, { driver_name: data.driver_name, status: data.status }];
          }
        });
      }
    });

    return () => {
      s.disconnect();
    };
  }, []);

  // Set driver status via HTTP POST
  async function setDriverStatus(driver, status) {
    try {
      const response = await fetch('/communication_send_driverconnectcommand', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User': localStorage.getItem('username') || ''
        },
        body: JSON.stringify({
          driver_name: driver,
          status: status
        })
      });

      const result = await response.json();
      if (response.ok) {
        console.log("Driver status update successful:", result);
      } else {
        alert("Driver status update failed: " + result.reason);
      }
    } catch (err) {
      console.error("Failed to send driver status update", err);
    }
  }

  return (
    <div>
      <h2>Driver Communications</h2>
      <div className="driver-list">
        {drivers.map(driverObj => {
          const { driver_name, status } = driverObj;
          return (
            <div className="driver-row" key={driver_name} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
              <span
                className={
                  "status-indicator " +
                  ((status === "online" || status === "connect")
                    ? "status-online"
                    : "status-offline")
                }
                style={{
                  display: "inline-block",
                  width: 12,
                  height: 12,
                  borderRadius: "50%",
                  background: (status === "online" || status === "connect") ? "green" : "gray"
                }}
              />
              <span className="driver-name" style={{ minWidth: 100 }}>{driver_name}</span>
              <span>
                {(status === "online" || status === "connect") ? "Online" : "Offline"}
              </span>
              <span className="driver-actions" style={{ marginLeft: "auto" }}>
                <button
                  onClick={() => setDriverStatus(driver_name, "connect")}
                  disabled={status === "online" || status === "connect"}
                >
                  Set Online
                </button>
                <button
                  onClick={() => setDriverStatus(driver_name, "disconnect")}
                  disabled={status === "offline" || status === "disconnect"}
                  style={{ marginLeft: 4 }}
                >
                  Set Offline
                </button>
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}