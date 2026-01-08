import React, { useState, useMemo, useEffect } from "react";
import { useLiveFeed } from "liveFeed";
import { useUserAction } from "../contexts/UserActionContext"; // <-- import


const MAX_EVENTS = 100;

function eventKey(event) {
  return (
    (event.track_id || "") +
    "_" +
    (event.timestamp || "") +
    "_" +
    (event.event_type || "")
  );
}

export default function TrackingView() {
  const [eventsObj] = useLiveFeed("tracking", "datafloweventmsg", eventKey);
  const {setPayload } = useUserAction(); // <-- get setter

  const [trackIdFilter, setTrackIdFilter] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");

  useEffect(() => {
    // Find the latest user_action event
    const userActionEvent = Object.values(eventsObj)
      .filter(e => e.event_type === "user_action")
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0];
    if (userActionEvent) {
      setPayload(userActionEvent.payload);
    }
  }, [eventsObj, setPayload]);

  // Convert to array and prepare filtered/sorted list
  const filteredEvents = useMemo(() => {
    return Object.values(eventsObj)
      .sort((a, b) => {
        const tA = new Date(a.timestamp || 0).getTime();
        const tB = new Date(b.timestamp || 0).getTime();
        return tB - tA;
      })
      .filter(
        (event) =>
          (trackIdFilter === "" ||
            (event.track_id || "")
              .toLowerCase()
              .includes(trackIdFilter.toLowerCase())) &&
          (eventTypeFilter === "" ||
            (event.event_type || "")
              .toLowerCase()
              .includes(eventTypeFilter.toLowerCase())) &&
          (sourceFilter === "" ||
            (event.source || "")
              .toLowerCase()
              .includes(sourceFilter.toLowerCase()))
      )
      .slice(0, MAX_EVENTS);
  }, [eventsObj, trackIdFilter, eventTypeFilter, sourceFilter]);

  return (
    <div>
      <h2>Data Flow Events</h2>

      {/* 🔍 Filter Bar */}
      <div
        style={{
          marginBottom: "1em",
          display: "flex",
          flexWrap: "wrap",
          gap: "0.5em",
        }}
      >
        <label>
          Track ID:{" "}
          <input
            type="text"
            value={trackIdFilter}
            onChange={(e) => setTrackIdFilter(e.target.value)}
            style={{ width: "14em" }}
          />
        </label>

        <label>
          Event Type:{" "}
          <input
            type="text"
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            style={{ width: "14em" }}
          />
        </label>

        <label>
          Source:{" "}
          <input
            type="text"
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            style={{ width: "14em" }}
          />
        </label>
      </div>

      {/* 📋 Events Table */}
      <table id="tracking-table" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ background: "#f8f8f8" }}>
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
            <tr
              key={eventKey(event) + "_" + idx}
              style={{
                borderBottom: "1px solid #ddd",
                verticalAlign: "top",
              }}
            >
              <td>{event.track_id || ""}</td>
              <td>{event.event_type || ""}</td>
              <td>{event.source || ""}</td>
              <td>{event.status || ""}</td>
              <td>{event.timestamp || ""}</td>
              <td>
                <pre
                  style={{
                    margin: 0,
                    whiteSpace: "pre-wrap",
                    fontSize: "0.85em",
                  }}
                >
                  {JSON.stringify(event.payload, null, 2)}
                </pre>
              </td>
            </tr>
          ))}
          {filteredEvents.length === 0 && (
            <tr>
              <td colSpan="6" style={{ textAlign: "center", padding: "1em" }}>
                No events to display
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
