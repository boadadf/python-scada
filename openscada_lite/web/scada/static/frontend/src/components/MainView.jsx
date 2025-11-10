import React, { useState } from "react";
import GisView from "./GisView";
import ImageView from "./ImageView";
import DatapointsView from "./DatapointsView";
import CommunicationsView from "./CommunicationsView";

export default function MainView() {
  const [subView, setSubView] = useState(null);
  const [subViewProp, setSubViewProp] = useState(null);

  // Handler for GIS marker navigation
  const handleMarkerClick = (path) => {
    if (!path) {
      setSubView(null);
      setSubViewProp(null);
      return;
    }

    // Example: "image/2_tank.svg" or "datapoint" or "communication"
    const [type, ...rest] = path.split("/");
    setSubView(type); // Set the subview type (e.g., "image", "datapoint", etc.)
    setSubViewProp(rest.length ? rest.join("/") : null); // Pass the remaining path as a prop
  };

  return (
    <div className="main-view">
      <div className="map-section">
        <GisView onMarkerClick={handleMarkerClick} />
      </div>
      <div className="subview-section">
        {subView === "image" && <ImageView selectedSvgProp={subViewProp} />}
        {subView === "datapoint" && <DatapointsView />}
        {subView === "communication" && <CommunicationsView />}
        {/* Add more views as needed */}
        {!subView && <div>Select a marker to view details below.</div>}
      </div>
    </div>
  );
}