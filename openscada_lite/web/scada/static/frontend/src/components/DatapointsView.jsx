import React, { useEffect, useState, useRef } from "react";
import { io } from "socket.io-client";

export default function DatapointsView() {
  const [datapoints, setDatapoints] = useState({});
  const socketRef = useRef(null);

  useEffect(() => {
    // Create socket when component mounts
    const socket = io();
    socketRef.current = socket;

    socket.on("connect", () => {
      socket.emit("datapoint_subscribe_live_feed");
    });

    // Receive initial datapoint list
    socket.on("datapoint_initial_state", tagList => {
      const list = Array.isArray(tagList) ? tagList : tagList ? [tagList] : [];
      const dpMap = {};
      list.forEach(tag => {
        dpMap[tag.datapoint_identifier] = tag;
      });
      setDatapoints(dpMap);
    });

    // Receive updates for individual datapoints
    socket.on("datapoint_tagupdatemsg", tag => {
      setDatapoints(prev => ({
        ...prev,
        [tag.datapoint_identifier]: {
          ...prev[tag.datapoint_identifier],
          ...tag
        }
      }));
    });

    // Clean up socket on unmount
    return () => {
      socket.disconnect();
    };
  }, []);

  async function sendUpdate(datapoint_identifier, value) {
    try {
      const response = await fetch("/datapoint_send_rawtagupdatemsg", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User": localStorage.getItem("username") || ""
        },
        body: JSON.stringify({
          datapoint_identifier,
          value,
          quality: "good"
        })
      });

      const result = await response.json();
      if (!response.ok) {
        alert("Update failed: " + result.reason);
      } else {
        console.log("Update successful:", result);
      }
    } catch (err) {
      console.error("Update request failed", err);
    }
  }

  return (
    <div>
      <h2>Tag List</h2>
      <table id="tag-table">
        <thead>
          <tr>
            <th>Tag</th>
            <th>Value</th>
            <th>Quality</th>
            <th>Timestamp</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {Object.values(datapoints).map(dp => {
            const valueDisplay =
              dp.value === undefined || dp.value === null ? "" : dp.value;
            const qualityDisplay = dp.quality ?? "None";
            const timestampDisplay = dp.timestamp ?? "None";

            return (
              <tr key={dp.datapoint_identifier}>
                <td>{dp.datapoint_identifier}</td>
                <td>
                  <input
                    type="text"
                    value={valueDisplay}
                    onChange={e => {
                      const val = e.target.value;
                      setDatapoints(prev => ({
                        ...prev,
                        [dp.datapoint_identifier]: {
                          ...prev[dp.datapoint_identifier],
                          value: val
                        }
                      }));
                    }}
                    onKeyDown={e => {
                      if (e.key === "Enter") {
                        sendUpdate(dp.datapoint_identifier, e.target.value);
                      }
                    }}
                  />
                </td>
                <td className="quality">{qualityDisplay}</td>
                <td className="timestamp">{timestampDisplay}</td>
                <td>
                  <button
                    onClick={() =>
                      sendUpdate(dp.datapoint_identifier, dp.value ?? "")
                    }
                  >
                    Update
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
