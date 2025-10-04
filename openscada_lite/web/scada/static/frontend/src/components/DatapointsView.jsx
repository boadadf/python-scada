import React, { useEffect, useState } from "react";
// Make sure to install socket.io-client: npm install socket.io-client
import { io } from "socket.io-client";

export default function DatapointsView() {
  const [datapoints, setDatapoints] = useState({});

  useEffect(() => {
    const socket = io();

    socket.on("connect", () => {
      socket.emit("datapoint_subscribe_live_feed");
    });

    socket.on("datapoint_initial_state", data => {
      // data is expected to be an array of datapoint objects
      const dpMap = {};
      (Array.isArray(data) ? data : []).forEach(dp => {
        dpMap[dp.datapoint_identifier] = dp;
      });
      setDatapoints(dpMap);
    });

    socket.on("datapoint_rawtagupdatemsg", msg => {
      // msg is a single datapoint update
      setDatapoints(prev => ({
        ...prev,
        [msg.datapoint_identifier]: {
          ...prev[msg.datapoint_identifier],
          ...msg
        }
      }));
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <div>
      <h2>Datapoints</h2>
      <table>
        <thead>
          <tr>
            <th>Identifier</th>
            <th>Value</th>
            <th>Quality</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {Object.values(datapoints).map(dp => (
            <tr key={dp.datapoint_identifier}>
              <td>{dp.datapoint_identifier}</td>
              <td>{dp.value !== undefined ? String(dp.value) : ""}</td>
              <td>{dp.quality || ""}</td>
              <td>{dp.timestamp || ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}