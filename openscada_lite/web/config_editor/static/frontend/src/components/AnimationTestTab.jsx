import React, { useEffect, useState, useRef } from "react";
import { gsap } from "gsap";
import { TextPlugin } from "gsap/TextPlugin";

gsap.registerPlugin(TextPlugin);

export default function AnimationTestTab() {
  const [svgList, setSvgList] = useState([]);
  const [selectedSvg, setSelectedSvg] = useState("");
  const [svgContent, setSvgContent] = useState("");
  const [datapoints, setDatapoints] = useState([]);
  const svgContainerRef = useRef(null);
  const socketRef = useRef(null);

  // --- Load list of SVGs on mount ---
  useEffect(() => {
    fetch("/api/animation/svgs")
      .then((r) => r.json())
      .then((svgs) => {
        setSvgList(svgs);
        if (svgs.length) setSelectedSvg(svgs[0]);
      });
  }, []);

  // --- Load selected SVG content ---
  useEffect(() => {
    if (!selectedSvg) return;
    fetch(`/svg/${selectedSvg}`)
      .then((r) => r.text())
      .then((svg) => {
        setSvgContent(svg);
        setTimeout(() => extractDatapoints(svg), 0);
      });
  }, [selectedSvg]);

  // --- Extract datapoints from the SVG content ---
  function extractDatapoints(svgText) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(svgText, "image/svg+xml");
    const elements = Array.from(doc.querySelectorAll("[data-datapoint]"));
    const points = elements.map((el) => el.getAttribute("data-datapoint"));
    const unique = [...new Set(points)];
    const dpObjs = unique.map((dp) => ({
      datapoint: dp,
      value: 0,
      quality: "good",
      alarm_status: "", // NEW
    }));
    setDatapoints(dpObjs);
  }

  // --- Setup live socket for animation updates ---
  useEffect(() => {
    let socket;
    if (!window.io) {
      const script = document.createElement("script");
      script.src = "https://cdn.socket.io/4.7.5/socket.io.min.js";
      script.onload = setupSocket;
      document.body.appendChild(script);
      return () => {
        if (socketRef.current) socketRef.current.disconnect();
        document.body.removeChild(script);
      };
    } else {
      setupSocket();
      return () => {
        if (socketRef.current) socketRef.current.disconnect();
      };
    }

    function setupSocket() {
      socket = window.io();
      socketRef.current = socket;
      socket.on("connect", () => {
        socket.emit("animation_subscribe_live_feed");
      });
      socket.on("animation_animationupdatemsg", (msg) => {
        if (!msg.test) return; // Only process test updates
        if (msg.svg_name !== selectedSvg) return;

        const svgElem = svgContainerRef.current;
        if (!svgElem) return;
        const elem = svgElem.querySelector(`#${msg.element_id}`);
        if (!elem || !msg.config) return;

        const cfg = { duration: msg.config.duration || 0.5 };
        if (msg.config.attr) cfg.attr = msg.config.attr;
        if (msg.config.text) cfg.text = msg.config.text;

        gsap.to(elem, cfg);
      });
    }
  }, [selectedSvg]);

  // --- Send test animation trigger ---
  function sendTest(dp) {
    const payload = {
      datapoint_identifier: dp.datapoint,
      quality: dp.quality || "good",
      value: dp.value,
      alarm_status: dp.alarm_status || null, // NEW
    };

    fetch("/animation_send_animationupdaterequestmsg", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then((r) => r.json())
      .then((res) => {
        console.log("Animation test sent:", res);
      })
      .catch((e) => console.error("Error sending test:", e));
  }

  return (
    <div style={{ display: "flex", gap: 16, padding: 12 }}>
      {/* --- Left: SVG Display --- */}
      <div style={{ flex: 0.7 }}>
        <h3>SVG Animation Test</h3>
        <select
          value={selectedSvg}
          onChange={(e) => setSelectedSvg(e.target.value)}
          style={{ marginBottom: 8 }}
        >
          {svgList.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>

        <div
          ref={svgContainerRef}
          dangerouslySetInnerHTML={{ __html: svgContent }}
          style={{
            border: "1px solid #ccc",
            background: "#f8f8f8",
            minHeight: 400,
            overflow: "auto",
          }}
        />
      </div>

      {/* --- Right: Test Controls --- */}
      <div style={{ flex: 1, minWidth: 520 }}>
        <h3>Datapoint / Alarm Controls</h3>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            border: "1px solid #ccc",
          }}
        >
          <thead>
            <tr style={{ background: "#eee" }}>
              <th>Datapoint</th>
              <th>Value</th>
              <th>Quality</th>
              <th>Alarm</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {datapoints.map((dp, i) => (
              <tr key={dp.datapoint}>
                <td style={{ fontSize: 12 }}>{dp.datapoint}</td>
                <td>
                  <input
                    type="text"
                    value={dp.value}
                    style={{ width: 80 }}
                    onChange={(e) =>
                      setDatapoints((prev) =>
                        prev.map((p, j) =>
                          j === i ? { ...p, value: e.target.value } : p
                        )
                      )
                    }
                  />
                </td>
                <td>
                  <select
                    value={dp.quality}
                    onChange={(e) =>
                      setDatapoints((prev) =>
                        prev.map((p, j) =>
                          j === i ? { ...p, quality: e.target.value } : p
                        )
                      )
                    }
                  >
                    <option value="good">good</option>
                    <option value="unknown">unknown</option>
                    <option value="bad">bad</option>
                  </select>
                </td>
                <td>
                  <select
                    value={dp.alarm_status || ""}
                    onChange={(e) =>
                      setDatapoints((prev) =>
                        prev.map((p, j) =>
                          j === i ? { ...p, alarm_status: e.target.value } : p
                        )
                      )
                    }
                  >
                    <option value="">(none)</option>
                    <option value="ACTIVE">ACTIVE</option>
                    <option value="ACK">ACK</option>
                    <option value="INACTIVE">INACTIVE</option>
                    <option value="FINISHED">FINISHED</option>
                  </select>
                </td>
                <td>
                  <button
                    onClick={() => sendTest(dp)}
                    style={{
                      background: "#007bff",
                      color: "white",
                      border: "none",
                      borderRadius: 4,
                      padding: "4px 8px",
                      cursor: "pointer",
                    }}
                  >
                    Test
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
