// src/contexts/AlertContext.jsx
import React, { createContext, useContext, useCallback } from "react";
import { useLiveFeed, postJson } from "../livefeed/openscadalite";

const AlertContext = createContext();
export const useAlert = () => useContext(AlertContext);

export const AlertProvider = ({ children }) => {
  // Use the library for live feed
  const [alerts] = useLiveFeed(
    "alert",
    "clientalertmsg",
    useCallback(a => a.track_id, [])
  );

  // Find the latest alert with show === true
  const alert = Object.values(alerts).find(a => a && a.show);

  // Use the library for POST
  const sendFeedback = async (trackId, feedback) => {
    try {
      await postJson("alert", "clientalertfeedbackmsg", { track_id: trackId, feedback });
      // Do not clear alert here; wait for server to send show: false
    } catch (err) {
      window.alert("Failed to send alert feedback: " + err.message);
    }
  };

  return (
    <AlertContext.Provider value={{ alert, sendFeedback }}>
      {children}
    </AlertContext.Provider>
  );
};
