import React, { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { TextPlugin } from "gsap/TextPlugin";
import { useLiveFeed, postJson } from "../livefeed/openscadalite";

gsap.registerPlugin(TextPlugin);

function animationKey(msg) {
  return (msg.svg_name || "") + "_" + (msg.element_id || "");
}

export default function ImageView({ selectedSvgProp, onSvgChange }) {
  const [svgList, setSvgList] = useState([]);
  const [selectedSvg, setSelectedSvg] = useState(selectedSvgProp || "");
  const [svgContent, setSvgContent] = useState("");
  const [svgExplanation, setSvgExplanation] = useState("");
  const svgContainerRef = useRef(null);

  // Sync external prop (from GIS or MainView)
  useEffect(() => {
    if (selectedSvgProp && selectedSvgProp !== selectedSvg) {
      setSelectedSvg(selectedSvgProp);
    }
  }, [selectedSvgProp]);

  // Notify parent if SVG changes
  useEffect(() => {
    if (onSvgChange) onSvgChange(selectedSvg);
  }, [selectedSvg, onSvgChange]);

  // Load list of available SVGs
  useEffect(() => {
    fetch("/api/animation/svgs")
      .then((r) => r.json())
      .then((svgs) => {
        setSvgList(svgs);
        if (!selectedSvg && svgs.length > 0) setSelectedSvg(svgs[0]);
      })
      .catch((err) => console.error("Failed to load SVG list:", err));
  }, []);

  // Load selected SVG content and explanation
  useEffect(() => {
    if (!selectedSvg) return;

    fetch(`/svg/${selectedSvg}`)
      .then((r) => r.text())
      .then((svg) => setSvgContent(svg))
      .catch((err) => console.error("Failed to load SVG:", err));

    const txtName = selectedSvg.replace(/\.svg$/i, ".txt");
    fetch(`/svg/${txtName}`)
      .then((r) => r.ok ? r.text() : Promise.reject("No explanation file"))
      .then((txt) => setSvgExplanation(txt.trim() || "No explanation available."))
      .catch((err) => {
        setSvgExplanation("No explanation available.");
        console.error("Failed to load SVG explanation:", err);
      });
  }, [selectedSvg]);

  // Live feed animations
  const [animations] = useLiveFeed("animation", "animationupdatemsg", animationKey);

  useEffect(() => {
    if (!svgContent) return;
    const svgElem = svgContainerRef.current;
    if (!svgElem) return;

    Object.values(animations).forEach((msg) => {
      if (!msg || msg.svg_name !== selectedSvg) return;

      const target = svgElem.querySelector(`#${msg.element_id}`);
      if (!target || !msg.config) return;

      const gsapConfig = { duration: msg.config.duration || 0.5 };
      if (msg.config.attr) gsapConfig.attr = msg.config.attr;
      if (msg.config.text) gsapConfig.text = msg.config.text;

      try {
        gsap.to(target, gsapConfig);
      } catch (err) {
        console.warn("Animation error:", err);
      }
    });
  }, [animations, svgContent, selectedSvg]);

  // Handle SVG clicks for commands
  useEffect(() => {
    const svgElem = svgContainerRef.current;
    if (!svgElem) return;

    function handleClick(e) {
      const target = e.target;
      if (!target) return;

      // Command → datapoint
      if (target.hasAttribute("command-datapoint")) {
        const command = target.getAttribute("command-datapoint");
        const value = target.getAttribute("command-value") || "";
        if (window.confirm(`Send command "${command}" with value "${value}"?`)) {
          const payload = {
            command_id: "cmd_" + Math.random().toString(36).slice(2),
            datapoint_identifier: command,
            value,
          };
          postJson("command", "sendcommandmsg", payload)
            .then((data) => window.alert(data?.reason || "Command sent!"))
            .catch((err) => window.alert("Error sending command: " + err.message));
        }
      }

      // Command → communication driver
      if (target.hasAttribute("command-communication")) {
        const driver = target.getAttribute("command-communication");
        const value = target.getAttribute("command-value") || "";
        if (window.confirm(`Send driver command "${driver}" = "${value}"?`)) {
          postJson("communication", "driverconnectcommand", {
            driver_name: driver,
            status: value,
          })
            .then((data) => window.alert(data?.reason || "Command sent!"))
            .catch((err) => window.alert("Error sending driver command: " + err.message));
        }
      }
    }

    svgElem.addEventListener("click", handleClick);
    return () => svgElem.removeEventListener("click", handleClick);
  }, [svgContent]);

  return (
    <div>
      <h2>Animated SVGs</h2>
      <select
        value={selectedSvg || ""}
        onChange={(e) => setSelectedSvg(e.target.value)}
        style={{ marginBottom: 8 }}
      >
        {svgList.map((svg) => (
          <option key={svg} value={svg}>
            {svg}
          </option>
        ))}
      </select>

      <div style={{ display: "flex", gap: 24 }}>
        <div
          id="svgContainer"
          ref={svgContainerRef}
          dangerouslySetInnerHTML={{ __html: svgContent }}
          style={{
            minHeight: 300,
            border: "1px solid #ccc",
            background: "#fafafa",
            borderRadius: 6,
            padding: 8,
            flex: 1,
          }}
        />
        <div style={{ minWidth: 250, maxWidth: 400 }}>
          <h3>Explanation</h3>
          <pre style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
            {svgExplanation || "No explanation available."}
          </pre>
        </div>
      </div>
    </div>
  );
}
