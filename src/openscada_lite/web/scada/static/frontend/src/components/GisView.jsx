// src/components/GisView.jsx
import React, { useEffect, useState, useCallback, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { useLiveFeed } from "liveFeed";
import { Api } from "generatedApi";

// Fix Leaflet default icons path
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Refresh map size when tab becomes visible
function MapRefresher({ active }) {
  const map = useMap();

  useEffect(() => {
    if (active && map) {
      setTimeout(() => map.invalidateSize(), 100);
    }
  }, [active, map]);

  return null;
}

export default function GisView({ active, onMarkerClick }) {
  const [gisConfig, setGisConfig] = useState(null);
  const markerRefs = useRef({});

  const markerKey = useCallback(
    (m) => `${m.id}_${m.latitude}_${m.longitude}`,
    []
  );

  /**
   * Live GIS markers via Socket.IO
   */
  const [markers] = useLiveFeed(
    "gis",
    "gisupdatemsg",
    markerKey
  );

  /**
   * Load GIS configuration via OpenAPI
   */
  useEffect(() => {
    let cancelled = false;
    const api = new Api(); // Ensure Api is instantiated

    async function loadConfig() {
      try {
        const res = await api.gis.getGisConfig();
        const cfg = res?.data;
        if (!cancelled && cfg) {
          setGisConfig(cfg);
        }
      } catch (err) {
        console.error("Failed to fetch GIS config:", err);
      }
    }

    loadConfig();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!gisConfig) {
    return <div>Loading GIS configuration...</div>;
  }

  const {
    baseurl,
    attribution,
    center_x,
    center_y,
    zoom,
  } = gisConfig;

  return (
    <div style={{ height: "100%", width: "100%" }}>
      <MapContainer
        center={[
          parseFloat(center_x),
          parseFloat(center_y),
        ]}
        zoom={zoom}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer attribution={attribution} url={baseurl} />

        <MapRefresher active={active} />

        {Object.values(markers).map((m) => {
          const key = markerKey(m);

          const icon = m.icon
            ? new L.Icon({
                iconUrl: m.icon,
                iconSize: [50, 50],
                iconAnchor: [25, 50],
              })
            : new L.Icon.Default();

          return (
            <Marker
              key={key}
              position={[m.latitude, m.longitude]}
              icon={icon}
              ref={(ref) => {
                markerRefs.current[key] = ref;
              }}
            >
              <Popup>
                <div>
                  <strong>{m.label || m.id}</strong>
                  <br />
                  Lat: {m.latitude.toFixed(4)}
                  <br />
                  Lon: {m.longitude.toFixed(4)}

                  {m.text && (
                    <>
                      <br />
                      <div
                        dangerouslySetInnerHTML={{
                          __html: m.text.replace(/\n/g, "<br>"),
                        }}
                      />
                    </>
                  )}

                  {m.navigation && onMarkerClick && (
                    <button
                      style={{ marginTop: 4 }}
                      onClick={() => {
                        onMarkerClick(
                          m.navigation,
                          m.navigation_type || "default"
                        );

                        const marker = markerRefs.current[key];
                        if (marker?.closePopup) {
                          marker.closePopup();
                        }
                      }}
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
