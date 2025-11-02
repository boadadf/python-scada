import React from "react";
import { NavLink } from "react-router-dom";

const tabs = [
  { label: "Image", path: "/image" },
  { label: "GIS", path: "/gis" },
  { label: "Datapoints", path: "/datapoints" },
  { label: "Communications", path: "/communications" },
  { label: "Alarms", path: "/alarms" },
  { label: "Commands", path: "/commands" },
  { label: "Tracking", path: "/tracking" }
];

export default function Tabs() {
  return (
    <div className="tabs">
      {tabs.map(tab => (
        <NavLink
          key={tab.path}
          to={tab.path}
          className={({ isActive }) => "tab-btn" + (isActive ? " active" : "")}
        >
          {tab.label}
        </NavLink>
      ))}
    </div>
  );
}