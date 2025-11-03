import React from "react";
import { useLiveFeed, postJson } from "../livefeed/openscadalite";

function driverKey(driver) {
  return driver.driver_name;
}

export default function CommunicationsView() {
  // Only live feed, no POST logic here
  const [driversObj] = useLiveFeed(
    "communication",
    "driverconnectstatus",
    driverKey
  );

  const drivers = Object.values(driversObj);

  // Set driver status via separated postJson helper
  async function setDriverStatus(driver, status) {
    try {
      await postJson("communication", "driverconnectcommand", {
        driver_name: driver,
        status: status,
      });
    } catch (err) {
      window.alert("Failed to send driver status update: " + err.message);
    }
  }

  return (
    <div>
      <h2>Driver Communications</h2>
      <div className="driver-list">
        {drivers.map((driverObj) => {
          const { driver_name, status } = driverObj;
          const isOnline = status === "online" || status === "connect";

          return (
            <div
              className="driver-row"
              key={driver_name}
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
                style={{ minWidth: 100, fontWeight: 500 }}
              >
                {driver_name}
              </span>
              <span>{isOnline ? "Online" : "Offline"}</span>
              <span className="driver-actions" style={{ marginLeft: "auto" }}>
                <button
                  onClick={() => setDriverStatus(driver_name, "connect")}
                  disabled={isOnline}
                >
                  Set Online
                </button>
                <button
                  onClick={() => setDriverStatus(driver_name, "disconnect")}
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
