import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import TopMenu from "./components/TopMenu";
import { useAuth, AuthProvider, Login } from "login";
import ImageView from "./components/ImageView";
import DatapointsView from "./components/DatapointsView";
import CommunicationsView from "./components/CommunicationsView";
import AlarmsView from "./components/AlarmsView";
import CommandsView from "./components/CommandsView";
import TrackingView from "./components/TrackingView";
import { AlertProvider } from "./contexts/AlertContext";
import AlertPopup from "./components/AlertPopup";


// Tab definitions
const TABS = [
  { key: "image", label: "Image", Component: ImageView },
  { key: "datapoints", label: "Datapoints", Component: DatapointsView },
  { key: "communications", label: "Communications", Component: CommunicationsView },
  { key: "alarms", label: "Alarms", Component: AlarmsView },
  { key: "commands", label: "Commands", Component: CommandsView },
  { key: "tracking", label: "Tracking", Component: TrackingView }
];

function PrivateApp() {
  const [activeTab, setActiveTab] = useState("image");
  const [alarmActive, setAlarmActive] = useState(false);
  const alarmBtnRef = useRef();

  useEffect(() => {
    function handleMessage(event) {
      if (event.data === "RaiseAlert:Alarms") setAlarmActive(true);
      if (event.data === "LowerAlert:Alarms") setAlarmActive(false);
    }
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  return (
    <div>
      <TopMenu />
      <div className="tabs">
        {TABS.map(tab => (
          <button
            key={tab.key}
            className={`tab-btn${activeTab === tab.key ? " active" : ""}`}
            data-tab={tab.key}
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
      {/* Render all tabs, only show the active one */}
      {TABS.map(tab => (
        <div
          key={tab.key}
          className={activeTab === tab.key ? "tab-content active" : "tab-content"}
          style={{ display: activeTab === tab.key ? "block" : "none" }}
        >
          <tab.Component />
        </div>
      ))}
    </div>
  );
}

function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    window.location.href = "/scada/login";
    return null;
  }
  return children;
}

export default function App() {
  const [route, setRoute] = useState(window.location.pathname);
  if (route === "/scada/login") {
    return (
      <AuthProvider>
        <Login redirectPath="/scada"/>
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