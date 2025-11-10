import React, { useEffect, useState, useRef } from "react";
import Hls from "hls.js";

export default function StreamView() {
  const [streams, setStreams] = useState([]);
  const [selectedStream, setSelectedStream] = useState(null);
  const videoRef = useRef(null);
  const hlsRef = useRef(null); // Reference to the HLS instance

  useEffect(() => {
    // Fetch the list of streams from the backend
    fetch("/streams")
      .then((response) => response.json())
      .then((data) => {
        setStreams(data);
        setSelectedStream(null); // Default to no stream selected
      })
      .catch((err) => console.error("Failed to load streams:", err));
  }, []);

  useEffect(() => {
    if (!selectedStream || !videoRef.current) return;

    const video = videoRef.current;
    const streamUrl = `${selectedStream.protocol}://${selectedStream.server || window.location.hostname}:${selectedStream.port}/${selectedStream.path}`;

    // Destroy the previous HLS instance if it exists
    if (hlsRef.current) {
      hlsRef.current.destroy();
      hlsRef.current = null;
    }

    if (Hls.isSupported()) {
      const hls = new Hls();
      hls.loadSource(streamUrl);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.muted = true; // Mute the video to allow autoplay
        video.play().catch((err) => console.error("Autoplay failed:", err));
      });

      hls.on(Hls.Events.ERROR, (event, data) => {
        console.error("HLS.js error:", data);
      });

      hlsRef.current = hls; // Save the HLS instance for cleanup
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      // For Safari and browsers with native HLS support
      video.src = streamUrl;
      video.muted = true; // Mute the video to allow autoplay
      video.play().catch((err) => console.error("Autoplay failed:", err));
    } else {
      console.error("HLS is not supported in this browser.");
    }
  }, [selectedStream]);

  return (
    <div>
      <h2>Streaming Cameras</h2>
      <select
        value={selectedStream?.id || ""}
        onChange={(e) => {
          const stream = streams.find((s) => s.id === e.target.value) || null;
          setSelectedStream(stream);
        }}
        style={{ marginBottom: 8 }}
      >
        <option value="">-- Select a Stream --</option> {/* Empty option */}
        {streams.map((stream) => (
          <option key={stream.id} value={stream.id}>
            {stream.description}
          </option>
        ))}
      </select>

      {selectedStream && (
        <div>
          <h3>{selectedStream.description}</h3>
          <video
            ref={videoRef}
            controls
            muted
            style={{ width: "100%", maxHeight: "500px", border: "1px solid #ccc" }}
          />
        </div>
      )}
    </div>
  );
}