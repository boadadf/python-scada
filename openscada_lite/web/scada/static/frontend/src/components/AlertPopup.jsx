// src/components/AlertPopup.jsx
import React from "react";
import { useAlert } from "../contexts/AlertContext";

const AlertPopup = () => {
  const { alert, sendFeedback } = useAlert();

  if (!alert) return null;

  const { message, alert_type, track_id } = alert;

  const handleFeedback = async (feedback) => {
    try {
      const response = await fetch("/alert_send_clientalertfeedbackmsg", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User": localStorage.getItem("username") || ""
        },
        body: JSON.stringify({
          track_id,
          feedback
        })
      });

      if (!response.ok) {
        const error = await response.json();
        alert("Failed to send alert feedback: " + (error.reason || response.status));
      }
    } catch (err) {
      console.error("Failed to send alert feedback", err);
    }

    // Always hide the popup after interaction
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
