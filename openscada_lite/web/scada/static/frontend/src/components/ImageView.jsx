// File: src/components/ImageView.jsx
import React, { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { TextPlugin } from "gsap/TextPlugin";
import { useLiveFeed, postJson } from "../livefeed/openscadalite";

gsap.registerPlugin(TextPlugin);

function animationKey(msg) {
  return (msg.svg_name || "") + "_" + (msg.element_id || "");
}

/**
 * ImageView
 * Props:
 * - selectedSvgProp: optional, name of svg (with or without .svg) selected from other parts of the app
 * - forcedSvg: optional, when present causes ImageView to load exactly that svg and hide the dropdown
 * - onSvgChange: optional callback(svgName) when selected svg changes
 */
export default function ImageView({ selectedSvgProp, onSvgChange, forcedSvg }) {
  const [svgList, setSvgList] = useState([]);
  const [selectedSvg, setSelectedSvg] = useState(""); // normalized name with .svg
  const [svgContent, setSvgContent] = useState("");
  const [svgExplanation, setSvgExplanation] = useState("");
  const svgContainerRef = useRef(null);

  // normalize helper: ensures name ends with .svg
  const normalizeSvgName = (name) => {
    if (!name) return "";
    return name.toLowerCase().endsWith(".svg") ? name : `${name}.svg`;
  };

  // Initialize selectedSvg when forcedSvg or selectedSvgProp changes
  useEffect(() => {
    if (forcedSvg) {
      setSelectedSvg(normalizeSvgName(forcedSvg));
      return;
    }
    if (selectedSvgProp) {
      setSelectedSvg(normalizeSvgName(selectedSvgProp));
    }
  }, [forcedSvg, selectedSvgProp]);

  // Load list of available svgs only when NOT forced
  useEffect(() => {
    if (forcedSvg) return;
    let cancelled = false;
    fetch("/api/animation/svgs")
      .then((r) => r.json())
      .then((svgs) => {
        if (cancelled) return;
        // Expecting an array of filenames (maybe with .svg)
        const normalized = svgs.map((s) => normalizeSvgName(s));
        setSvgList(normalized);
        // If no selection yet, pick first
        setSelectedSvg((prev) => (prev ? prev : normalized[0] || ""));
      })
      .catch(() => {
        if (!cancelled) setSvgList([]);
      });
    return () => (cancelled = true);
  }, [forcedSvg]);

  // Fetch SVG content + explanation when selectedSvg changes
  useEffect(() => {
    if (!selectedSvg) {
      setSvgContent("");
      setSvgExplanation("");
      return;
    }

    const svgPath = `/config/svg/${selectedSvg}`;
    const txtPath = `/config/svg/${selectedSvg.replace(/\.svg$/i, ".txt")}`;

    // fetch svg
    let cancelled = false;
    fetch(svgPath)
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error("not found"))))
      .then((text) => {
        if (cancelled) return;
        setSvgContent(text);
      })
      .catch(() => {
        if (!cancelled) setSvgContent("");
      });

    // fetch explanation
    fetch(txtPath)
      .then((r) => (r.ok ? r.text() : Promise.reject(new Error("no txt"))))
      .then((txt) => {
        if (cancelled) return;
        setSvgExplanation((txt && txt.trim()) || "No explanation available.");
      })
      .catch(() => {
        if (!cancelled) setSvgExplanation("No explanation available.");
      });

    return () => (cancelled = true);
  }, [selectedSvg]);

  // Inform parent of selection changes
  useEffect(() => {
    if (onSvgChange) onSvgChange(selectedSvg);
  }, [selectedSvg, onSvgChange]);

  // Live feed animations
  const [animations] = useLiveFeed("animation", "animationupdatemsg", animationKey);

  // Apply animations after svgContent is present and DOM mounted
  useEffect(() => {
    if (!svgContent) return;
    // Wait a tick so innerHTML is applied and DOM nodes exist
    const raf = requestAnimationFrame(() => {
      const svgElem = svgContainerRef.current;
      if (!svgElem) return;

      Object.values(animations || {}).forEach((msg) => {
        if (!msg || msg.svg_name !== selectedSvg) return;

        const target = svgElem.querySelector(`#${msg.element_id}`);
        if (!target || !msg.config) return;

        const gsapConfig = { duration: msg.config.duration || 0.5 };
        if (msg.config.attr) gsapConfig.attr = msg.config.attr;
        if (msg.config.text) gsapConfig.text = msg.config.text;

        try {
          gsap.to(target, gsapConfig);
        } catch (err) {
          // don't crash the app; log
          // console.warn("Animation error:", err);
        }
      });
    });

    return () => cancelAnimationFrame(raf);
  }, [animations, svgContent, selectedSvg]);

  // Click handler for SVG commands - reattached when svgContent changes
  useEffect(() => {
    const svgElem = svgContainerRef.current;
    if (!svgElem) return;

    function handleClick(e) {
      const target = e.target;
      if (!target) return;

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
            .catch((err) => window.alert("Error sending command: " + err?.message));
        }
      }

      if (target.hasAttribute("command-communication")) {
        const driver = target.getAttribute("command-communication");
        const value = target.getAttribute("command-value") || "";
        if (window.confirm(`Send driver command "${driver}" = "${value}"?`)) {
          postJson("communication", "driverconnectcommand", {
            driver_name: driver,
            status: value,
          })
            .then((data) => window.alert(data?.reason || "Command sent!"))
            .catch((err) => window.alert("Error sending driver command: " + err?.message));
        }
      }
    }

    svgElem.addEventListener("click", handleClick);
    return () => svgElem.removeEventListener("click", handleClick);
  }, [svgContent]);

  return (
    <div>
      <h2>Animated SVGs</h2>

      {/* Dropdown shown only when not forced */}
      {!forcedSvg && (
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
      )}

      {/* Small label when forced mode is active */}
      {forcedSvg && (
        <div style={{ marginBottom: 8, fontWeight: "bold" }}>{normalizeSvgName(forcedSvg)}</div>
      )}

      <div style={{ display: "flex", gap: 24 }}>
        <div
          id="svgContainer"
          ref={svgContainerRef}
          // svgContent contains full SVG markup (string)
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
