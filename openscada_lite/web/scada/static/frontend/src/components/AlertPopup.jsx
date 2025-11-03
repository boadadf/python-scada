// src/components/AlertPopup.jsx
import React from "react";
import { useAlert } from "../contexts/AlertContext";

const AlertPopup = () => {
  const { alert, sendFeedback } = useAlert();

  if (!alert) return null;

  const { message, alert_type, track_id } = alert;

  const handleFeedback = (feedback) => {
    sendFeedback(track_id, feedback);
  };

  return (
    <div className="popup-overlay">
      <div className="popup">
        <p>{message}</p>

        {alert_type === "accept" && (
          <button onClick={() => handleFeedback("accept")}>Accept</button>
        )}

        {alert_type === "confirm_cancel" && (
          <>
            <button onClick={() => handleFeedback("confirm")}>Confirm</button>
            <button onClick={() => handleFeedback("cancel")}>Cancel</button>
          </>
        )}
      </div>
    </div>
  );
};

export default AlertPopup;
