import React from "react";
import { useLiveFeed, postJson } from "../livefeed/openscadalite";

function datapointKey(dp) {
  return dp.datapoint_identifier;
}

export default function DatapointsView() {
  // Only live feed, no POST logic here
  const [datapoints, setDatapoints] = useLiveFeed(
    "datapoint",
    "tagupdatemsg",
    datapointKey
  );

  // Send update via separated postJson helper
  async function sendUpdate(datapoint_identifier, value) {
    try {
      await postJson("datapoint", "rawtagupdatemsg", {
        datapoint_identifier,
        value,
        quality: "good",
      });
    } catch (err) {
      window.alert("Update failed: " + err.message);
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
          {Object.values(datapoints).map((dp) => {
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
                    onChange={(e) => {
                      const val = e.target.value;
                      setDatapoints((prev) => ({
                        ...prev,
                        [dp.datapoint_identifier]: {
                          ...prev[dp.datapoint_identifier],
                          value: val,
                        },
                      }));
                    }}
                    onKeyDown={(e) => {
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
