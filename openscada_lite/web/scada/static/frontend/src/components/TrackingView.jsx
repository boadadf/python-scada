import React, { useState } from "react";
import { useLiveFeed } from "../livefeed/useLiveFeed";

const MAX_EVENTS = 100;

function eventKey(event) {
  // Use a composite key for uniqueness
  return (event.track_id || "") + "_" + (event.timestamp || "") + "_" + (event.event_type || "");
}

export default function TrackingView() {
  const [eventsObj] = useLiveFeed(
    "tracking",
    "datafloweventmsg",
    eventKey
  );
  // Convert to array and sort by timestamp descending (optional)
  const events = Object.values(eventsObj)
    .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
    .slice(0, MAX_EVENTS);

  const [trackIdFilter, setTrackIdFilter] = useState("");
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");

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
            <tr key={eventKey(event) + "_" + idx}>
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