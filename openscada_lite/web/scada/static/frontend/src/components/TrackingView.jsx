import React, { useEffect, useState, useRef } from "react";
import { io } from "socket.io-client";

const MAX_EVENTS = 100;

export default function TrackingView() {
  const [events, setEvents] = useState([]);
  const [trackIdFilter, setTrackIdFilter] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const socketRef = useRef(null);

  useEffect(() => {
    const socket = io();
    socketRef.current = socket;

    socket.on("connect", () => {
      socket.emit("tracking_subscribe_live_feed");
    });

    socket.on("tracking_initial_state", eventList => {
      setEvents(Array.isArray(eventList) ? eventList.slice(0, MAX_EVENTS) : []);
    });

    socket.on("tracking_datafloweventmsg", event => {
      setEvents(prev => [event, ...prev].slice(0, MAX_EVENTS));
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  // Filter logic
  const filteredEvents = events.filter(event =>
    (trackIdFilter === "" || (event.track_id || "").toLowerCase().includes(trackIdFilter.toLowerCase())) &&
    (eventTypeFilter === "" || (event.event_type || "").toLowerCase().includes(eventTypeFilter.toLowerCase())) &&
    (sourceFilter === "" || (event.source || "").toLowerCase().includes(sourceFilter.toLowerCase()))
  );

  return (
    <div>
      <h2>Data Flow Events</h2>
      <div style={{ marginBottom: "1em" }}>
        <label>
          Track ID:{" "}
          <input
            type="text"
            value={trackIdFilter}
            onChange={e => setTrackIdFilter(e.target.value)}
            style={{ marginRight: "1em", width: "16em" }}
          />
        </label>
        <label>
          Event Type:{" "}
          <input
            type="text"
            value={eventTypeFilter}
            onChange={e => setEventTypeFilter(e.target.value)}
            style={{ marginRight: "1em", width: "16em" }}
          />
        </label>
        <label>
          Source:{" "}
          <input
            type="text"
            value={sourceFilter}
            onChange={e => setSourceFilter(e.target.value)}
            style={{ width: "16em" }}
          />
        </label>
      </div>
      <table id="tracking-table">
        <thead>
          <tr>
            <th>Track ID</th>
            <th>Event Type</th>
            <th>Source</th>
            <th>Status</th>
            <th>Timestamp</th>
            <th>Payload</th>
          </tr>
        </thead>
        <tbody>
          {filteredEvents.map((event, idx) => (
            <tr key={event.track_id + event.timestamp + idx}>
              <td>{event.track_id || ""}</td>
              <td>{event.event_type || ""}</td>
              <td>{event.source || ""}</td>
              <td>{event.status || ""}</td>
              <td>{event.timestamp || ""}</td>
              <td>
                <pre style={{ margin: 0 }}>
                  {JSON.stringify(event.payload, null, 2)}
                </pre>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}