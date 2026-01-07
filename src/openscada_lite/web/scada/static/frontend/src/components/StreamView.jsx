import React, { useEffect, useRef, useState } from "react";
import Hls from "hls.js";
import { Api } from "generatedApi";

export default function StreamView({ selectedStreamId }) {
  const [streams, setStreams] = useState([]);
  const [selectedStream, setSelectedStream] = useState(null);
  const videoRef = useRef(null);
  const hlsRef = useRef(null);

  // Load streams from backend via OpenAPI client
  useEffect(() => {
    const api = new Api();
    async function loadStreams() {
      try {
        const res = await api.streams.getStreams();
        const data = res.streams ?? res.data ?? res;
        if (!Array.isArray(data)) {
          throw new Error("listStreams did not return an array");
        }

        setStreams(data);
      } catch (err) {
        console.error("Failed to load streams:", err);
      }
    }
    loadStreams();
  }, []);

  // React to external selection
  useEffect(() => {
    if (!selectedStreamId || streams.length === 0) return;

    const found = streams.find(
      (s) => s.id === selectedStreamId || s.path === selectedStreamId
    );

    console.log("🎯 Selecting stream from prop:", selectedStreamId, found);

    if (found) setSelectedStream(found);
  }, [selectedStreamId, streams]);

  // Play selected stream
  useEffect(() => {
    if (!selectedStream || !videoRef.current) return;

    const video = videoRef.current;
    const streamUrl = `${selectedStream.protocol}://${selectedStream.server || window.location.hostname}:${selectedStream.port}/${selectedStream.path}`;

    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(streamUrl);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.muted = true;
        video.play().catch((e) => console.error("Autoplay failed:", e));
      });
      hlsRef.current = hls;
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = streamUrl;
      video.muted = true;
      video.play().catch((e) => console.error("Autoplay failed:", e));
    }
  }, [selectedStream]);

  return (
    <div>
      <h2>Streaming Cameras</h2>
      <select
        value={selectedStream?.id || ""}
        onChange={(e) => {
          const s = streams.find((st) => st.id === e.target.value);
          setSelectedStream(s);
        }}
        style={{ marginBottom: 8 }}
      >
        <option value="">-- Select Stream --</option>
        {streams.map((s) => (
          <option key={s.id} value={s.id}>
            {s.description}
          </option>
        ))}
      </select>

      {selectedStream && (
        <>
          <h3>{selectedStream.description}</h3>
          <video
            ref={videoRef}
            controls
            muted
            style={{
              width: "100%",
              maxHeight: "500px",
              border: "1px solid #ccc",
            }}
          />
        </>
      )}
    </div>
  );
}
