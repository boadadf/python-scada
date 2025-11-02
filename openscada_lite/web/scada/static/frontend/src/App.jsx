import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import TopMenu from "./components/TopMenu";
import { useAuth, AuthProvider, Login } from "login";
import ImageView from "./components/ImageView";
import GisView from "./components/GisView";
import DatapointsView from "./components/DatapointsView";
import CommunicationsView from "./components/CommunicationsView";
import AlarmsView from "./components/AlarmsView";
import CommandsView from "./components/CommandsView";
import TrackingView from "./components/TrackingView";
import { AlertProvider } from "./contexts/AlertContext";
import AlertPopup from "./components/AlertPopup";
import "leaflet/dist/leaflet.css";

// ---------------------------------------------
// Tab definitions
// ---------------------------------------------
const TABS = [
  { key: "gis", label: "GIS", Component: GisView },
  { key: "image", label: "Image", Component: ImageView },
  { key: "datapoints", label: "Datapoints", Component: DatapointsView },
  { key: "communications", label: "Communications", Component: CommunicationsView },
  { key: "alarms", label: "Alarms", Component: AlarmsView },
  { key: "commands", label: "Commands", Component: CommandsView },
  { key: "tracking", label: "Tracking", Component: TrackingView },
];

// ---------------------------------------------
// Main private app (after login)
// ---------------------------------------------
function PrivateApp() {
  const [activeTab, setActiveTab] = useState("gis");
  const [alarmActive, setAlarmActive] = useState(false);
  const [selectedSvg, setSelectedSvg] = useState(null); // for ImageView dropdown
  const alarmBtnRef = useRef();

  useEffect(() => {
    function handleMessage(event) {
      if (event.data === "RaiseAlert:Alarms") setAlarmActive(true);
      if (event.data === "LowerAlert:Alarms") setAlarmActive(false);
    }
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  // 🔹 Handler for GIS markers that navigate to Image tab
  const handleMarkerClick = (navigatePath) => {
    // Remove 'image/' or any leading folder from the path
    let svgName = navigatePath;
    if (svgName && svgName.includes("/")) {
      svgName = svgName.split("/").pop();
    }
    setSelectedSvg(svgName); // tell ImageView which SVG to select
    setActiveTab("image");   // switch to Image tab
  };

  return (
    <div className="app-container">
      <TopMenu />

      <div className="tabs">
        {TABS.map(tab => (
          <button
            key={tab.key}
            className={`tab-btn${activeTab === tab.key ? " active" : ""}`}
            onClick={() => setActiveTab(tab.key)}
            ref={tab.key === "alarms" ? alarmBtnRef : undefined}
            style={
              tab.key === "alarms" && alarmActive
                ? { background: "red", color: "white" }
                : {}
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Keep all components mounted; only show the active one */}
      {TABS.map(tab => (
        <div
          key={tab.key}
          className="tab-content"
          style={{ display: activeTab === tab.key ? "block" : "none" }}
        >
          {tab.key === "gis" ? (
            <tab.Component active={activeTab === "gis"} onMarkerClick={handleMarkerClick} />
          ) : tab.key === "image" ? (
            <tab.Component selectedSvgProp={selectedSvg} />
          ) : (
            <tab.Component />
          )}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------
// Authentication wrapper
// ---------------------------------------------
function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    window.location.href = "/scada/login";
    return null;
  }
  return children;
}

// ---------------------------------------------
// Root App Component
// ---------------------------------------------
export default function App() {
  const [route] = useState(window.location.pathname);

  if (route === "/scada/login") {
    return (
      <AuthProvider>
        <Login redirectPath="/scada" />
      </AuthProvider>
    );
  }

  return (
    <AuthProvider>
      <RequireAuth>
        <AlertProvider>
          <PrivateApp />
          <AlertPopup />
        </AlertProvider>
      </RequireAuth>
    </AuthProvider>
  );
}
