// src/components/DatapointsView.jsx
import React, { useCallback } from "react";
import { useLiveFeed } from "liveFeed";
import { Api } from "generatedApi";

function datapointKey(dp) {
  return dp.datapoint_identifier;
}

export default function DatapointsView() {
  /**
   * Live datapoint updates (Socket.IO)
   */
  const [datapoints, setDatapoints] = useLiveFeed(
    "datapoint",
    "tagupdatemsg",
    datapointKey
  );

  /**
   * Send manual tag update via OpenAPI
   */
  const sendUpdate = useCallback(
    async (datapoint_identifier, value) => {
      const api = new Api();
      try {
        await api.datapoint.rawtagupdatemsg({
          datapoint_identifier,
          value,
          quality: "good",
        });
      } catch (err) {
        window.alert(
          "Update failed: " + (err?.message ?? "Unknown error")
        );
      }
    },
    []
  );

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
              dp.value === undefined || dp.value === null
                ? ""
                : dp.value;

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
                        sendUpdate(
                          dp.datapoint_identifier,
                          e.target.value
                        );
                      }
                    }}
                  />
                </td>

                <td className="quality">
                  {qualityDisplay}
                </td>

                <td className="timestamp">
                  {timestampDisplay}
                </td>

                <td>
                  <button
                    onClick={() =>
                      sendUpdate(
                        dp.datapoint_identifier,
                        dp.value ?? ""
                      )
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
