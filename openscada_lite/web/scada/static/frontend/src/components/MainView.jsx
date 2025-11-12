import React, { useState, useEffect } from "react";
import GisView from "./GisView";
import ImageView from "./ImageView";
import StreamView from "./StreamView";
import DatapointsView from "./DatapointsView";
import CommunicationsView from "./CommunicationsView";

export default function MainView() {
  const [rightPanelView, setRightPanelView] = useState(null);
  const [viewProp, setViewProp] = useState(null);
  const [popupContent, setPopupContent] = useState(null); // For popup content
  const [popupVisible, setPopupVisible] = useState(false); // Popup visibility

  // 🔹 This runs when you click a marker
  const handleMarkerClick = (navigation, navigationType) => {
    if (!navigation) {
      setRightPanelView(null);
      setViewProp(null);
      setPopupVisible(false);
      return;
    }

    const [type, ...rest] = navigation.split("/");
    const navType = type?.trim().toLowerCase();
    const navValue = rest.join("/").trim();

    console.log("🧭 Marker clicked:", { navType, navValue, navigationType });

    if (navigationType === "popup") {
      // Handle popup navigation
      setPopupContent({ navType, navValue });
      setPopupVisible(true);
    } else {
      // Handle right panel navigation
      if (navType === "image") {
        setRightPanelView("image");
        setViewProp(navValue);
      } else if (navType === "stream") {
        setRightPanelView("stream");
        setViewProp(navValue);
      } else if (navType === "datapoint") {
        setRightPanelView("datapoint");
        setViewProp(navValue);
      } else if (navType === "communication") {
        setRightPanelView("communication");
        setViewProp(navValue);
      } else {
        console.warn("❌ Unknown navigation type:", navigation);
      }
    }
  };

  useEffect(() => {
    console.log("📺 Right panel changed:", rightPanelView, viewProp);
  }, [rightPanelView, viewProp]);

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: "8px",
        height: "calc(100vh - 120px)",
      }}
    >
      {/* Left - Map */}
      <div style={{ borderRadius: "8px", overflow: "hidden", border: "1px solid #ccc" }}>
        <GisView
          onMarkerClick={(navigation, navigationType) => {
            const [type, ...rest] = navigation.split("/");
            const navType = type?.trim().toLowerCase();
            const navValue = rest.join("/").trim();

            console.log("🧭 Marker clicked:", { navType, navValue, navigationType });

            handleMarkerClick(navigation, navigationType); // Pass navigationType directly
          }}
        />
      </div>

      {/* Right - Dynamic panel */}
      <div
        className="right-panel"
        style={{ flex: 1, paddingLeft: 16, overflowY: "auto" }}
      >
        {rightPanelView === "image" && (
          <ImageView key={`image-${viewProp}`} selectedSvgProp={viewProp} />
        )}
        {rightPanelView === "stream" && (
          <StreamView key={`stream-${viewProp}`} selectedStreamId={viewProp} />
        )}
        {rightPanelView === "datapoint" && (
          <DatapointsView key={`datapoint-${viewProp}`} />
        )}
        {rightPanelView === "communication" && (
          <CommunicationsView key={`comm-${viewProp}`} />
        )}
        {!rightPanelView && (
          <div style={{ textAlign: "center", marginTop: "20px" }}>
            Select a marker to view details here.
          </div>
        )}
      </div>

      {/* Floating Popup */}
      {popupVisible && popupContent && (
        <div
          className="floating-popup"
          style={{
            position: "fixed",
            top: "20%",
            left: "50%",
            transform: "translate(-50%, -20%)",
            background: "white",
            border: "1px solid #ccc",
            borderRadius: "8px",
            padding: "16px",
            zIndex: 1000,
            boxShadow: "0 4px 8px rgba(0, 0, 0, 0.2)",
          }}
        >
          <button
            style={{
              position: "absolute",
              top: "8px",
              right: "8px",
              background: "red",
              color: "white",
              border: "none",
              borderRadius: "50%",
              width: "24px",
              height: "24px",
              cursor: "pointer",
            }}
            onClick={() => setPopupVisible(false)}
          >
            &times;
          </button>
          {popupContent.navType === "image" && (
            <ImageView key={`popup-image-${popupContent.navValue}`} selectedSvgProp={popupContent.navValue} />
          )}
          {popupContent.navType === "stream" && (
            <StreamView key={`popup-stream-${popupContent.navValue}`} selectedStreamId={popupContent.navValue} />
          )}
          {popupContent.navType === "datapoint" && (
            <DatapointsView key={`popup-datapoint-${popupContent.navValue}`} />
          )}
          {popupContent.navType === "communication" && (
            <CommunicationsView key={`popup-comm-${popupContent.navValue}`} />
          )}
        </div>
      )}
    </div>
  );
}