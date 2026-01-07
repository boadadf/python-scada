import React, { useCallback } from "react";
import { useAlert } from "../contexts/AlertContext";

export default function AlertPopup() {
  const { alert, sendFeedback } = useAlert();

  // No alert → render nothing
  if (!alert) return null;

  const { message, alert_type, track_id } = alert;

  const handleFeedback = useCallback(
    (feedback) => {
      sendFeedback(track_id, feedback);
    },
    [sendFeedback, track_id]
  );

  return (
    <div className="popup-overlay">
      <div className="popup">
        <p>{message}</p>

        {alert_type === "accept" && (
          <button onClick={() => handleFeedback("accept")}>
            Accept
          </button>
        )}

        {alert_type === "confirm_cancel" && (
          <div className="popup-actions">
            <button onClick={() => handleFeedback("confirm")}>
              Confirm
            </button>
            <button onClick={() => handleFeedback("cancel")}>
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
