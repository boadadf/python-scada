import React, { useEffect, useCallback } from "react";
import { useLiveFeed } from "liveFeed";
import { Api } from "generatedApi";

function formatTime(val) {
  return val || "None";
}

export default function AlarmsView() {
  /**
   * Stable key generator
   */
  const alarmKey = useCallback(
    (alarm) =>
      alarm.alarm_occurrence_id ||
      `${alarm.datapoint_identifier}@${alarm.activation_time}`,
    []
  );

  /**
   * Live alarms via Socket.IO
   * (Correctly NOT part of OpenAPI)
   */
  const [alarmsObj] = useLiveFeed(
    "alarm",
    "alarmupdatemsg",
    alarmKey
  );

  const alarms = Object.values(alarmsObj);

  const activeAlarms = alarms.filter(
    (alarm) => !(alarm.deactivation_time && alarm.acknowledge_time)
  );

  /**
   * Notify parent window if unacknowledged alarms exist
   */
  useEffect(() => {
    const hasUnack = activeAlarms.some(
      (alarm) => !alarm.acknowledge_time
    );

    window.parent.postMessage(
      hasUnack ? "RaiseAlert:Alarms" : "LowerAlert:Alarms",
      "*"
    );
  }, [activeAlarms]);

  /**
   * Acknowledge alarm via OpenAPI client
   */
  async function sendAck(alarm_occurrence_id) {
    try {
      const api = new Api();
      console.log("Sending ack:", { alarm_occurrence_id });
      await api.alarm.ackalarmmsg({
        alarm_occurrence_id
      });
    } catch (err) {
      alert(
        "Ack failed: " + (err?.message ?? "Unknown error")
      );
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
          {activeAlarms.map((alarm) => {
            const key = alarmKey(alarm);

            return (
              <tr key={key}>
                <td>{alarm.rule_id || "N/A"}</td>
                <td>{alarm.datapoint_identifier}</td>
                <td>{formatTime(alarm.activation_time)}</td>
                <td>{formatTime(alarm.deactivation_time)}</td>
                <td>{formatTime(alarm.acknowledge_time)}</td>
                <td>
                  <button
                    onClick={() =>
                      sendAck(alarmKey(alarm))
                    }
                  >
                    Ack
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
