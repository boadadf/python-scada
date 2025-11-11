import React, { useState, useEffect } from "react";
import GisView from "./GisView";
import ImageView from "./ImageView";
import StreamView from "./StreamView";
import DatapointsView from "./DatapointsView";
import CommunicationsView from "./CommunicationsView";

export default function MainView() {
  const [rightPanelView, setRightPanelView] = useState(null);
  const [viewProp, setViewProp] = useState(null);

  // 🔹 This runs when you click a marker
  const handleMarkerClick = (navigation) => {
    if (!navigation) {
      setRightPanelView(null);
      setViewProp(null);
      return;
    }

    const [type, ...rest] = navigation.split("/");
    const navType = type?.trim().toLowerCase();
    const navValue = rest.join("/").trim();

    console.log("🧭 Marker clicked:", { navType, navValue });

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
        <GisView onMarkerClick={handleMarkerClick} />
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
    </div>
  );
}
