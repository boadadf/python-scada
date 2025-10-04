import React, { useEffect, useState, useCallback } from "react";

// Helper to format time
function formatTime(val) {
  return val ? val : "None";
}

export default function AlarmsView() {
  const [alarms, setAlarms] = useState({});

  // Add or update an alarm in state
  const updateAlarm = useCallback(alarm => {
    const id = alarm.alarm_occurrence_id || (alarm.datapoint_identifier + "@" + alarm.activation_time);
    // If finished, remove it
    if (alarm.deactivation_time && alarm.acknowledge_time) {
      setAlarms(prev => {
        const copy = { ...prev };
        delete copy[id];
        return copy;
      });
      return;
    }
    setAlarms(prev => ({ ...prev, [id]: alarm }));
  }, []);

  // Remove an alarm from state
  const removeAlarm = useCallback(id => {
    setAlarms(prev => {
      const copy = { ...prev };
      delete copy[id];
      return copy;
    });
  }, []);

  // Send Ack
  async function sendAck(alarm_occurrence_id) {
    try {
      const response = await fetch("/alarm_send_ackalarmmsg", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User": localStorage.getItem("username") || ""
        },
        body: JSON.stringify({ alarm_occurrence_id })
      });
      const result = await response.json();
      if (!response.ok) {
        alert("Ack failed: " + result.reason);
      }
    } catch (err) {
      alert("Failed to send ack: " + err.message);
    }
  }

  // Alarm highlight logic (RaiseAlert/LowerAlert)
  useEffect(() => {
    const hasUnack = Object.values(alarms).some(alarm => !alarm.acknowledge_time);
    window.parent.postMessage(
      hasUnack ? "RaiseAlert:Alarms" : "LowerAlert:Alarms",
      "*"
    );
  }, [alarms]);

  // Socket.IO logic
  useEffect(() => {
    // Dynamically load socket.io if not already loaded
    let socket;
    let script = document.createElement("script");
    script.src = "https://cdn.socket.io/4.7.5/socket.io.min.js";
    script.onload = () => {
      // global io now available
      socket = window.io();
      socket.on("connect", () => {
        socket.emit("alarm_subscribe_live_feed");
      });

      socket.on("alarm_initial_state", alarmList => {
        const list = Array.isArray(alarmList) ? alarmList : alarmList ? [alarmList] : [];
        const newAlarms = {};
        for (const alarm of list) {
          const id = alarm.alarm_occurrence_id || (alarm.datapoint_identifier + "@" + alarm.activation_time);
          newAlarms[id] = alarm;
        }
        setAlarms(newAlarms);
      });

      socket.on("alarm_alarmupdatemsg", alarmList => {
        const list = Array.isArray(alarmList) ? alarmList : alarmList ? [alarmList] : [];
        const newAlarms = {};
        for (const alarm of list) {
          const id = alarm.alarm_occurrence_id || (alarm.datapoint_identifier + "@" + alarm.activation_time);
          newAlarms[id] = alarm;
        }
        setAlarms(newAlarms);
      });
    };
    document.body.appendChild(script);

    return () => {
      if (socket) socket.disconnect();
      document.body.removeChild(script);
    };
  }, []);

  return (
    <div>
      <h2>Active Alarms</h2>
      <table id="alarm-table">
        <thead>
          <tr>
            <th>Rule ID</th>
            <th>Datapoint</th>
            <th>Activation Time</th>
            <th>Deactivation Time</th>
            <th>Acknowledge Time</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(alarms).map(([id, alarm]) => (
            <tr key={id}>
              <td>{alarm.rule_id || "N/A"}</td>
              <td>{alarm.datapoint_identifier}</td>
              <td>{formatTime(alarm.activation_time)}</td>
              <td>{formatTime(alarm.deactivation_time)}</td>
              <td>{formatTime(alarm.acknowledge_time)}</td>
              <td>
                <button onClick={() => sendAck(id)}>Ack</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}