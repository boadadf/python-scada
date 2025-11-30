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

// Map tab names to components
const TAB_COMPONENTS = {
  Main: MainView,
  Image: ImageView,
  Datapoints: DatapointsView,
  Communications: CommunicationsView,
  Alarms: AlarmsView,
  Commands: CommandsView,
  Tracking: TrackingView,
  Streams: StreamView
};

// ---------------------------------------------
// Private SCADA App (shown after login)
// ---------------------------------------------
function PrivateApp() {
  const [activeTab, setActiveTab] = useState("Main");
  const [alarmActive, setAlarmActive] = useState(false);
  const [selectedSvg, setSelectedSvg] = useState(null);
  const [tabs, setTabs] = useState([]);
  const alarmBtnRef = useRef();

  useEffect(() => {
    // Fetch tabs from backend
    fetch("/frontend/api/tabs")
      .then(res => res.json())
      .then(setTabs);
  }, []);

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
    setActiveTab("Main");
  };

  return (
    <div className="app-container">
      <TopMenu />

      <div className="tabs">
        {tabs.map(tab => (
          <button
            key={tab}
            className={`tab-btn${activeTab === tab ? " active" : ""}`}
            onClick={() => setActiveTab(tab)}
            ref={tab === "Alarms" ? alarmBtnRef : undefined}
            style={tab === "Alarms" && alarmActive ? { background: "red", color: "white" } : {}}
          >
            {tab}
          </button>
        ))}
      </div>

      {tabs.map(tab => {
        const Component = TAB_COMPONENTS[tab];
        if (!Component) return null;
        return (
          <div
            key={tab}
            className="tab-content"
            style={{ display: activeTab === tab ? "block" : "none" }}
          >
            {tab === "Image" ? (
              <Component selectedSvgProp={selectedSvg} />
            ) : tab === "Main" ? (
              <Component active={activeTab === "Main"} onMarkerClick={handleMarkerClick} />
            ) : (
              <Component />
            )}
          </div>
        );
      })}

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
