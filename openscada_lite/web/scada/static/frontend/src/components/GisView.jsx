import React, { useEffect, useCallback } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { useLiveFeed } from "../livefeed/openscadalite";

// 🧩 Fix Leaflet default icons path issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// ✅ Helper to refresh map size when the tab becomes visible
function MapRefresher({ active }) {
  const map = useMap();
  useEffect(() => {
    if (active && map) setTimeout(() => map.invalidateSize(), 300);
  }, [active, map]);
  return null;
}

export default function GisView({ active, onMarkerClick }) {
  // ✅ useCallback prevents socket reconnection loops
  const markerKey = useCallback(
    (m) => m.id + "_" + m.latitude + "_" + m.longitude,
    []
  );

  const [markers] = useLiveFeed("gis", "gisupdatemsg", markerKey);

  const baseUrl =
    "https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg";

  return (
    <div
      style={{
        height: "calc(100vh - 120px)",
        width: "100%",
        background: "#f0f0f0",
        borderRadius: "8px",
        overflow: "hidden",
      }}
    >
      <MapContainer
        center={[47.4233, 8.3064]} // Niederrohrdorf
        zoom={16}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.swisstopo.admin.ch/">swisstopo</a> & OpenStreetMap'
          url={baseUrl}
        />

        <MapRefresher active={active} />

        {Object.values(markers).map((m) => {
          const icon = m.icon
            ? new L.Icon({
                iconUrl: m.icon,
                iconSize: [50, 50],
                iconAnchor: [25, 50],
              })
            : new L.Icon.Default();

          return (
            <Marker
              key={markerKey(m)}
              position={[m.latitude, m.longitude]}
              icon={icon}
            >
              <Popup>
                <div>
                  <strong>{m.label || m.id}</strong>
                  <br />
                  Lat: {m.latitude.toFixed(4)} <br />
                  Lon: {m.longitude.toFixed(4)} <br />
                  {m.navigation && onMarkerClick && (
                    <button
                      style={{ marginTop: "4px" }}
                      onClick={() => onMarkerClick(m.navigation)}
                    >
                      Go to {m.navigation.split("/").pop()}
                    </button>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
