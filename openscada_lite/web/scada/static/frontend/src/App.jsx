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
import { AlertProvider } from "./contexts/AlertContext";
import { UserActionProvider } from "./contexts/UserActionContext";
import AlertPopup from "./components/AlertPopup";
import StreamView from "./components/StreamView";
import MainView from "./components/MainView";
import "leaflet/dist/leaflet.css";

const TAB_COMPONENTS = {
  GIS: MainView,
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
  const [alarmActive, setAlarmActive] = useState(false);
  const [selectedSvg, setSelectedSvg] = useState(null); // for ImageView when using dropdown mode
  const [tabs, setTabs] = useState([]); // normalized tab objects
  const alarmBtnRef = useRef();

  useEffect(() => {
    // fetch tab array from backend
    fetch("/frontend/api/tabs")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("no tabs"))))
      .then((fetched) => {
        // fetched is expected to be array of strings like ["Main","Image","Image(stress_test)"]
        const normalized = fetched.map((t, idx) => {
          if (typeof t !== "string") return { key: `tab_${idx}`, label: String(t), raw: t };
          const imageMatch = /^Image\(([^)]+)\)$/i.exec(t.trim());
          if (imageMatch) {
            const svgName = imageMatch[1];
            // key unique per forced image tab
            return { key: `Image:${svgName}`, label: "Image", forcedSvg: svgName, raw: t };
          }
          // plain Image without forced svg
          if (t.trim().toLowerCase() === "image") {
            return { key: `Image:all`, label: "Image", forcedSvg: null, raw: t };
          }
          // other tabs
          return { key: t, label: t, forcedSvg: null, raw: t };
        });

        setTabs(normalized);

        // determine initial active tab: prefer first tab, otherwise Main
        const initial = normalized[0] || { key: "Main", label: "Main" };
        setActiveTabKey(initial.key);
      })
      .catch(() => {
        // fallback to default tabs
        const defaults = [
          { key: "Main", label: "Main", forcedSvg: null },
          { key: "Image:all", label: "Image", forcedSvg: null },
        ];
        setTabs(defaults);
        setActiveTabKey(defaults[0].key);
      });
  }, []);

  useEffect(() => {
    function handleMessage(event) {
      if (event.data === "RaiseAlert:Alarms") setAlarmActive(true);
      if (event.data === "LowerAlert:Alarms") setAlarmActive(false);
    }
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  // Called by MainView markers when user wants to navigate to an SVG
  const handleMarkerClick = (navigatePath) => {
    let svgName = navigatePath;
    if (svgName && svgName.includes("/")) svgName = svgName.split("/").pop();
    // set selection for dropdown-mode ImageView
    setSelectedSvg(svgName);
    // if there's a plain Image tab, switch to that; otherwise switch to first Image tab
    const plainImage = tabs.find((t) => t.label === "Image" && t.forcedSvg === null);
    const anyImage = tabs.find((t) => t.label === "Image");
    const targetKey = plainImage ? plainImage.key : anyImage ? anyImage.key : activeTabKey;
    setActiveTabKey(targetKey);
  };

  return (
    <div className="app-container">
      <TopMenu />

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

      {tabs.map((t) => {
        const Component = TAB_COMPONENTS[t.label];
        if (!Component) return null;

        return (
          <div
            key={t.key + "_content"}
            className="tab-content"
            style={{ display: activeTabKey === t.key ? "block" : "none" }}
          >
            {t.label === "Image" ? (
              // pass forcedSvg when present, also pass selectedSvgProp for dropdown-mode
              <ImageView forcedSvg={t.forcedSvg} selectedSvgProp={t.forcedSvg ? t.forcedSvg : selectedSvg} onSvgChange={(s) => { /* no-op or store if needed */ }} />
            ) : t.label === "Main" ? (
              <Component active={activeTabKey === t.key} onMarkerClick={handleMarkerClick} />
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
