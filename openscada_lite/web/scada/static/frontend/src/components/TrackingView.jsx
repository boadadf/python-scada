import React, { useEffect, useState } from "react";
// Make sure to install socket.io-client: npm install socket.io-client
import { io } from "socket.io-client";

export default function TrackingView() {
  const [tracking, setTracking] = useState([]);

  useEffect(() => {
    const socket = io();

    socket.on("connect", () => {
      socket.emit("tracking_subscribe_live_feed");
    });

    socket.on("tracking_initial_state", data => {
      setTracking(Array.isArray(data) ? data : []);
    });

    socket.on("tracking_trackingmsg", msg => {
      setTracking(prev => [msg, ...prev]);
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <div>
      <h2>Tracking Events</h2>
      <table>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Type</th>
            <th>Source</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {tracking.map((event, idx) => (
            <tr key={idx}>
              <td>{event.timestamp || ""}</td>
              <td>{event.type || ""}</td>
              <td>{event.source || ""}</td>
              <td>{event.message || ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}