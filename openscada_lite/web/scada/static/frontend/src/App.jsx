import React, { Suspense, useState, useEffect, useRef } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import "./App.css";
import Login from "./components/Login";

// Lazy load your views for code splitting
const ImageView = React.lazy(() => import("./components/ImageView"));
const DatapointsView = React.lazy(() => import("./components/DatapointsView"));
const CommunicationsView = React.lazy(() => import("./components/CommunicationsView"));
const AlarmsView = React.lazy(() => import("./components/AlarmsView"));
const CommandsView = React.lazy(() => import("./components/CommandsView"));
const TrackingView = React.lazy(() => import("./components/TrackingView"));

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

  // Listen for messages from iframes (RaiseAlert/LowerAlert)
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
      <Suspense fallback={<div style={{padding: 40, textAlign: "center"}}>Loading...</div>}>
        {TABS.map(tab =>
          activeTab === tab.key ? (
            <div key={tab.key} className="tab-content active">
              <tab.Component />
            </div>
          ) : null
        )}
      </Suspense>
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
        <Login />
      </AuthProvider>
    );
  }

  return (
    <AuthProvider>
      <RequireAuth>
        <PrivateApp />
      </RequireAuth>
    </AuthProvider>
  );
}