// src/contexts/AlertContext.jsx
// src/contexts/AlertContext.jsx
import React, { createContext, useContext, useCallback } from "react";
import { useLiveFeed } from "liveFeed";
import { Api } from "generatedApi"; // <-- your typed OpenAPI client

const AlertContext = createContext();

export const useAlert = () => {
  const ctx = useContext(AlertContext);
  if (!ctx) throw new Error("useAlert must be used within AlertProvider");
  return ctx;
};

export const AlertProvider = ({ children }) => {
  // Live feed for alerts
  const [alerts] = useLiveFeed(
    "alert",
    "clientalertmsg",
    useCallback((a) => a.track_id, [])
  );

  // Find latest alert with show === true
  const alert = Object.values(alerts).find((a) => a && a.show);

  // Send alert feedback (using OpenAPI client)
  const sendFeedback = async (trackId, feedback) => {
    const api = new Api();
    try {
      await api.alert.clientalertfeedbackmsg({
        track_id: trackId,
        feedback,
      });
      // Alert state will be updated from server via live feed
    } catch (err) {
      console.error("Failed to send alert feedback:", err);
      window.alert("Failed to send alert feedback: " + (err?.message || err));
    }
  };

  return (
    <AlertContext.Provider value={{ alert, sendFeedback }}>
      {children}
    </AlertContext.Provider>
  );
};
