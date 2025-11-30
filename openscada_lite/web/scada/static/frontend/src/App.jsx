import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import TopMenu from "./components/TopMenu";
import StatusBar from "./components/StatusBar";
import { AuthProvider, useAuth, Login } from "login";
import ImageView from "./components/ImageView";
import DatapointsView from "./components/DatapointsView";
import CommunicationsView from "./components/CommunicationsView";
import AlarmsView from "./components/AlarmsView";
import CommandsView from "./components/CommandsView";
import TrackingView from "./components/TrackingView";
import { AlertProvider } from "./contexts/AlertContext";
import { UserActionProvider } from "./contexts/UserActionContext";
import AlertPopup from "./components/AlertPopup";
import StreamView from "./components/StreamView";
import MainView from "./components/MainView";
import "leaflet/dist/leaflet.css";

// ---------------------------------------------
// Tab definitions
// ---------------------------------------------
const TABS = [
  { key: "main", label: "Main", Component: MainView },
  { key: "image", label: "Image", Component: ImageView },
  { key: "datapoints", label: "Datapoints", Component: DatapointsView },
  { key: "communications", label: "Communications", Component: CommunicationsView },
  { key: "alarms", label: "Alarms", Component: AlarmsView },
  { key: "commands", label: "Commands", Component: CommandsView },
  { key: "tracking", label: "Tracking", Component: TrackingView },
  { key: "streams", label: "Streams", Component: StreamView }
];

// ---------------------------------------------
// Private SCADA App (shown after login)
// ---------------------------------------------
function PrivateApp() {
  const [activeTab, setActiveTab] = useState("main");
  const [alarmActive, setAlarmActive] = useState(false);
  const [selectedSvg, setSelectedSvg] = useState(null);
  const alarmBtnRef = useRef();

  useEffect(() => {
    function handleMessage(event) {
      if (event.data === "RaiseAlert:Alarms") setAlarmActive(true);
      if (event.data === "LowerAlert:Alarms") setAlarmActive(false);
    }
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  const handleMarkerClick = (navigatePath) => {
    let svgName = navigatePath;
    if (svgName && svgName.includes("/")) svgName = svgName.split("/").pop();
    setSelectedSvg(svgName);
    setActiveTab("main");
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
            style={tab.key === "alarms" && alarmActive ? { background: "red", color: "white" } : {}}
          >
            {tab.label}
          </button>
        ))}
      </div>

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

      <StatusBar />
    </div>
  );
}

// ---------------------------------------------
// Auth Wrapper (like security-editor)
// ---------------------------------------------
function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) return null; // don't render anything until auth is known

  if (!isAuthenticated) {
    return <Login redirectPath="/scada" />;
  }

  return children;
}

// ---------------------------------------------
// Root SCADA App
// ---------------------------------------------
export default function App() {
  return (
    <AuthProvider>
      <RequireAuth>
        <AlertProvider>
          <UserActionProvider>
            <PrivateApp />
            <AlertPopup />
          </UserActionProvider>
        </AlertProvider>
      </RequireAuth>
    </AuthProvider>
  );
}
