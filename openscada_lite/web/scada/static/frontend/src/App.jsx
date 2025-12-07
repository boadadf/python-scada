import React, { useEffect, useRef, useState } from "react";
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
import StreamView from "./components/StreamView";
import MainView from "./components/MainView";
import { AlertProvider } from "./contexts/AlertContext";
import { UserActionProvider } from "./contexts/UserActionContext";
import AlertPopup from "./components/AlertPopup";

const TAB_COMPONENTS = {
  Main: MainView,
  Image: ImageView,
  Datapoints: DatapointsView,
  Communications: CommunicationsView,
  Alarms: AlarmsView,
  Commands: CommandsView,
  Tracking: TrackingView,
  Streams: StreamView,
};

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

function RequireAuth({ children }) {
  const { isAuthenticated, loading } = useAuth();
  if (loading) return null;
  if (!isAuthenticated) return <Login redirectPath="/scada" />;
  return children;
}

function PrivateApp() {
  const [activeTabKey, setActiveTabKey] = useState(null);
  const [tabs, setTabs] = useState([]);
  const [selectedSvg, setSelectedSvg] = useState(null);
  const [alarmActive, setAlarmActive] = useState(false);
  const alarmBtnRef = useRef();

  useEffect(() => {
    // fetch tab array from backend
    fetch("/frontend/api/tabs")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("no tabs"))))
      .then((fetched) => {
        const normalized = fetched.map((t, idx) => {
          if (typeof t !== "string") return { key: `tab_${idx}`, label: String(t), raw: t };

          const imageMatch = /^Image\(([^)]+)\)$/i.exec(t.trim());
          if (imageMatch) {
            return { key: `Image:${imageMatch[1]}`, label: "Image", forcedSvg: imageMatch[1], raw: t };
          }
          if (t.trim().toLowerCase() === "image") {
            return { key: `Image:all`, label: "Image", forcedSvg: null, raw: t };
          }
          return { key: t, label: t, forcedSvg: null, raw: t };
        });

        setTabs(normalized);
        setActiveTabKey(normalized[0]?.key || "Main");
      })
      .catch(() => {
        const defaults = [
          { key: "Main", label: "Main", forcedSvg: null },
          { key: "Image:all", label: "Image", forcedSvg: null },
        ];
        setTabs(defaults);
        setActiveTabKey(defaults[0].key);
      });
  }, []);

  useEffect(() => {
    const handleMessage = (event) => {
      if (event.data === "RaiseAlert:Alarms") setAlarmActive(true);
      if (event.data === "LowerAlert:Alarms") setAlarmActive(false);
    };
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  const handleMarkerClick = (navigatePath) => {
    let svgName = navigatePath;
    if (svgName && svgName.includes("/")) svgName = svgName.split("/").pop();
    setSelectedSvg(svgName);

    const plainImage = tabs.find((t) => t.label === "Image" && t.forcedSvg === null);
    const anyImage = tabs.find((t) => t.label === "Image");
    const targetKey = plainImage ? plainImage.key : anyImage ? anyImage.key : activeTabKey;
    setActiveTabKey(targetKey);
  };

  return (
    <div className="app-container">
      <TopMenu />

      {/* Tabs */}
      <div className="tabs">
        {tabs.map((t) => (
          <button
            key={t.key}
            className={`tab-btn${activeTabKey === t.key ? " active" : ""}`}
            onClick={() => setActiveTabKey(t.key)}
            ref={t.label === "Alarms" ? alarmBtnRef : undefined}
            style={t.label === "Alarms" && alarmActive ? { background: "red", color: "white" } : {}}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tabs.map((t) => {
        const Component = TAB_COMPONENTS[t.label];
        if (!Component) return null;

        const isActive = activeTabKey === t.key;
        return (
          <div
            key={t.key + "_content"}
            className="tab-content"
            style={{ display: isActive ? "block" : "none", height: "calc(100vh - 120px)" }}
          >
            {t.label === "Image" ? (
              <ImageView
                forcedSvg={t.forcedSvg}
                selectedSvgProp={t.forcedSvg ? t.forcedSvg : selectedSvg}
              />
            ) : t.label === "Main" ? (
              <Component active={isActive} onMarkerClick={handleMarkerClick} />
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
