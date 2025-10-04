import React, { useEffect, useState, useRef } from "react";

// Make sure to install socket.io-client: npm install socket.io-client
import { io } from "socket.io-client";

export default function CommandsView() {
  const [commands, setCommands] = useState({});
  const socketRef = useRef(null);

  // Setup Socket.IO and live updates
  useEffect(() => {
    const socket = io();
    socketRef.current = socket;

    socket.on("connect", () => {
      socket.emit("command_subscribe_live_feed");
    });

    socket.on("command_initial_state", cmdList => {
      const list = Array.isArray(cmdList) ? cmdList : cmdList ? [cmdList] : [];
      const newCommands = {};
      list.forEach(cmd => {
        newCommands[cmd.datapoint_identifier] = cmd;
      });
      setCommands(newCommands);
    });

    socket.on("command_commandfeedbackmsg", cmd => {
      setCommands(prev => ({
        ...prev,
        [cmd.datapoint_identifier]: {
          ...prev[cmd.datapoint_identifier],
          ...cmd
        }
      }));
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  // Send command via HTTP POST
  async function sendCommand(datapoint_identifier, value) {
    try {
      const command_id = 'cmd_' + Math.random().toString(36).substring(2, 10);
      const response = await fetch('/command_send_sendcommandmsg', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User': localStorage.getItem('username') || ''
        },
        body: JSON.stringify({
          command_id,
          datapoint_identifier,
          value
        })
      });
      const result = await response.json();
      if (!response.ok) {
        alert("Command failed: " + result.reason);
      }
    } catch (err) {
      alert("Failed to send command: " + err.message);
    }
  }

  // Render
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
          {Object.values(commands).map(cmd => {
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
                    onChange={e => {
                      const val = e.target.value;
                      setCommands(prev => ({
                        ...prev,
                        [cmd.datapoint_identifier]: {
                          ...prev[cmd.datapoint_identifier],
                          value: val
                        }
                      }));
                    }}
                    onKeyDown={e => {
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