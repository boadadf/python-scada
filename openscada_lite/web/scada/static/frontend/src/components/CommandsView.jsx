import React, { useState } from "react";
import { useLiveFeed, postJson } from "../livefeed/openscadalite";

function commandKey(cmd) {
  return cmd.datapoint_identifier;
}

export default function CommandsView() {
  // Only live feed, no POST logic here
  const [commands, setCommands] = useLiveFeed(
    "command",
    "commandfeedbackmsg",
    commandKey
  );

  // Send command via separated postJson helper
  async function sendCommand(datapoint_identifier, value) {
    try {
      const command_id = "cmd_" + Math.random().toString(36).substring(2, 10);
      await postJson("command", "sendcommandmsg", {
        command_id,
        datapoint_identifier,
        value,
      });
    } catch (err) {
      window.alert("Failed to send command: " + err.message);
    }
  }

  return (
    <div>
      <h2>Command List</h2>
      <table id="command-table">
        <thead>
          <tr>
            <th>Command</th>
            <th>Value</th>
            <th>Feedback</th>
            <th>Timestamp</th>
            <th>Send</th>
          </tr>
        </thead>
        <tbody>
          {Object.values(commands).map((cmd) => {
            const valueDisplay = cmd.value ?? "";
            const feedbackDisplay = cmd.feedback ?? "None";
            const timestampDisplay = cmd.timestamp ?? "None";

            return (
              <tr key={cmd.datapoint_identifier}>
                <td>{cmd.datapoint_identifier}</td>
                <td>
                  <input
                    type="text"
                    value={valueDisplay}
                    onChange={(e) => {
                      const val = e.target.value;
                      setCommands((prev) => ({
                        ...prev,
                        [cmd.datapoint_identifier]: {
                          ...prev[cmd.datapoint_identifier],
                          value: val,
                        },
                      }));
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        sendCommand(cmd.datapoint_identifier, e.target.value);
                      }
                    }}
                  />
                </td>
                <td className="feedback">{feedbackDisplay}</td>
                <td className="timestamp">{timestampDisplay}</td>
                <td>
                  <button
                    onClick={() =>
                      sendCommand(cmd.datapoint_identifier, cmd.value)
                    }
                  >
                    Send
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
