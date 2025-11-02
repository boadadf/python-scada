// src/components/AlertPopup.jsx
import React from "react";
import { useAlert } from "../contexts/AlertContext";
import { useLiveFeed } from "../livefeed/useLiveFeed";

const AlertPopup = () => {
  const { alert, sendFeedback } = useAlert();
  const [, , postJson] = useLiveFeed("alert", "clientalertfeedbackmsg", () => {}, "clientalertfeedbackmsg");

  if (!alert) return null;

  const { message, alert_type, track_id } = alert;

  const handleFeedback = async (feedback) => {
    try {
      await postJson({ track_id, feedback });
    } catch (err) {
      alert("Failed to send alert feedback: " + err.message);
    }
    sendFeedback(); // Clears alert from context
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
