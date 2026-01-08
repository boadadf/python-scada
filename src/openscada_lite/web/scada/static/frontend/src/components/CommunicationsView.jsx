// src/components/CommunicationsView.jsx
import React, { useCallback } from "react";
import { useLiveFeed } from "liveFeed";
import { Api } from "generatedApi";

function driverKey(driver) {
  return driver.driver_name;
}

export default function CommunicationsView() {
  /**
   * Live driver status feed (Socket.IO)
   */
  const [driversObj] = useLiveFeed(
    "communication",
    "driverconnectstatus",
    driverKey
  );

  const drivers = Object.values(driversObj);
  const api = new Api();
  /**
   * Set driver status via OpenAPI client
   */
  const setDriverStatus = useCallback(
    async (driver_name, status) => {
      try {
        await api.communication.driverconnectcommand({
          driver_name,
          status,
        });
      } catch (err) {
        window.alert(
          "Failed to send driver status update: " +
            (err?.message ?? "Unknown error")
        );
      }
    },
    []
  );

  return (
    <div>
      <h2>Driver Communications</h2>

      <div className="driver-list">
        {drivers.map((driverObj) => {
          const { driver_name, status } = driverObj;
          const isOnline =
            status === "online" || status === "connect";

          return (
            <div
              key={driver_name}
              className="driver-row"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                marginBottom: 8,
              }}
            >
              <span
                className="status-indicator"
                style={{
                  display: "inline-block",
                  width: 12,
                  height: 12,
                  borderRadius: "50%",
                  background: isOnline ? "green" : "gray",
                }}
              />

              <span
                className="driver-name"
                style={{
                  minWidth: 100,
                  fontWeight: 500,
                }}
              >
                {driver_name}
              </span>

              <span>
                {isOnline ? "Online" : "Offline"}
              </span>

              <span
                className="driver-actions"
                style={{ marginLeft: "auto" }}
              >
                <button
                  onClick={() =>
                    setDriverStatus(driver_name, "connect")
                  }
                  disabled={isOnline}
                >
                  Set Online
                </button>

                <button
                  onClick={() =>
                    setDriverStatus(driver_name, "disconnect")
                  }
                  disabled={!isOnline}
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
