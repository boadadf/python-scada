import React, { useEffect } from "react";
import { useLiveFeed } from "../livefeed/useLiveFeed";

function formatTime(val) {
  return val ? val : "None";
}
function alarmKey(alarm) {
  return alarm.alarm_occurrence_id || (alarm.datapoint_identifier + "@" + alarm.activation_time);
}

export default function AlarmsView() {
  // 4th param: postType = "ackalarmmsg"
  const [alarmsObj, , postJson] = useLiveFeed("alarm", "alarmupdatemsg", alarmKey, "ackalarmmsg");
  const alarms = Object.values(alarmsObj);

  const activeAlarms = alarms.filter(
    alarm => !(alarm.deactivation_time && alarm.acknowledge_time)
  );

  useEffect(() => {
    const hasUnack = activeAlarms.some(alarm => !alarm.acknowledge_time);
    window.parent.postMessage(
      hasUnack ? "RaiseAlert:Alarms" : "LowerAlert:Alarms",
      "*"
    );
  }, [activeAlarms]);

  async function sendAck(alarm_occurrence_id) {
    try {
      await postJson({ alarm_occurrence_id });
    } catch (err) {
      alert("Ack failed: " + err.message);
    }
  }

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
          {activeAlarms.map(alarm => (
            <tr key={alarmKey(alarm)}>
              <td>{alarm.rule_id || "N/A"}</td>
              <td>{alarm.datapoint_identifier}</td>
              <td>{formatTime(alarm.activation_time)}</td>
              <td>{formatTime(alarm.deactivation_time)}</td>
              <td>{formatTime(alarm.acknowledge_time)}</td>
              <td>
                <button onClick={() => sendAck(alarmKey(alarm))}>Ack</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}