// src/contexts/AlertContext.jsx
import React, { createContext, useContext, useState, useEffect, useRef } from "react";
import { io } from "socket.io-client";

const AlertContext = createContext();
export const useAlert = () => useContext(AlertContext);

export const AlertProvider = ({ children }) => {
  const [alert, setAlert] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    const socket = io();
    socketRef.current = socket;

    socket.on("connect", () => {
      socket.emit("alert_subscribe_live_feed");
    });

    // Handle initial alert state (e.g., on page load or reconnect)
    socket.on("alert_initial_state", (alertList) => {
      const alerts = Array.isArray(alertList) ? alertList : [alertList];
      const latestVisible = alerts.find((a) => a.show);
      if (latestVisible) {
        setAlert(latestVisible);
      }
    });

    // Handle new alerts
    socket.on("alert_clientalertmsg", (data) => {
      if (data.show === false) {
        setAlert(null); // Hide alert
      } else {
        setAlert(data); // Show new alert
      }
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const sendFeedback = (trackId, feedback) => {
    if (!socketRef.current) return;
    socketRef.current.emit("CLIENT_ALERT_FEEDBACK", {
      track_id: trackId,
      feedback: feedback,
    });
    setAlert(null);
  };

  return (
    <AlertContext.Provider value={{ alert, sendFeedback }}>
      {children}
    </AlertContext.Provider>
  );
};
