import React from "react";
import { useLiveFeed } from "../livefeed/useLiveFeed";

function driverKey(driver) {
  return driver.driver_name;
}

export default function CommunicationsView() {
  // 4th param: postType = "driverconnectcommand"
  const [driversObj, , postJson] = useLiveFeed(
    "communication",
    "driverconnectstatus",
    driverKey,
    "driverconnectcommand"
  );
  const drivers = Object.values(driversObj);

  // Set driver status via unified postJson
  async function setDriverStatus(driver, status) {
    try {
      await postJson({
        driver_name: driver,
        status: status
      });
    } catch (err) {
      alert("Failed to send driver status update: " + err.message);
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