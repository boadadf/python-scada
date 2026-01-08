import React, { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { TextPlugin } from "gsap/TextPlugin";
import { useLiveFeed } from "liveFeed";
import { Api } from "generatedApi";

gsap.registerPlugin(TextPlugin);

function animationKey(msg) {
  return (msg.svg_name || "") + "_" + (msg.element_id || "");
}

export default function ImageView({ selectedSvgProp, onSvgChange, forcedSvg }) {
  const [svgList, setSvgList] = useState([]);
  const [selectedSvg, setSelectedSvg] = useState("");
  const [svgContent, setSvgContent] = useState("");
  const [svgExplanation, setSvgExplanation] = useState("");
  const svgContainerRef = useRef(null);

  const normalizeSvgName = (name) => (!name ? "" : name.toLowerCase().endsWith(".svg") ? name : `${name}.svg`);

  useEffect(() => {
    if (forcedSvg) {
      setSelectedSvg(normalizeSvgName(forcedSvg));
      return;
    }
    if (selectedSvgProp) {
      setSelectedSvg(normalizeSvgName(selectedSvgProp));
    }
  }, [forcedSvg, selectedSvgProp]);

  // Load list of SVGs via OpenAPI
  useEffect(() => {
    if (forcedSvg) return;

    let cancelled = false;
    const api = new Api();

    async function loadSvgList() {
      try {
        const response = await api.animation.getSvgs(); // Use the instantiated object
        console.log("Response from getSvgs:", response); // Log API response

        if (!cancelled) {
          const svgs = response?.data; // Extract the data property
          console.log("Fetched SVG list:", svgs); // Log fetched SVG list

          if (Array.isArray(svgs)) {
            const normalized = svgs.map(normalizeSvgName);
            setSvgList(normalized);
            console.log("Normalized SVG list:", normalized); // Log normalized SVG list

            setSelectedSvg((prev) => prev || normalized[0] || "");
          } else {
            console.error("Expected an array but received:", svgs);
            setSvgList([]);
          }
        }
      } catch (err) {
        if (!cancelled) setSvgList([]);
        console.error("Failed to load SVG list:", err);
      }
    }

    loadSvgList();
    return () => {
      cancelled = true;
    };
  }, [forcedSvg]);

  // Fetch SVG content and explanation via OpenAPI
  useEffect(() => {
    if (!selectedSvg) {
      setSvgContent("");
      setSvgExplanation("");
      return;
    }

    console.log("Selected SVG:", selectedSvg); // Log selected SVG

    let cancelled = false;
    const api = new Api();

    async function loadSvg() {
      try {
        const response = await api.animation.getSvg(selectedSvg);
        const content = await response.text(); // Parse response as text
        console.log("SVG content:", content); // Log SVG content
        if (!cancelled) setSvgContent(content);
      } catch (err) {
        console.error("Failed to load SVG content:", err);
        if (!cancelled) setSvgContent("");
      }

      try {
        const response = await api.animation.getSvg(selectedSvg.replace(/\.svg$/i, ".txt"));
        const explanation = await response.text(); // Parse explanation as text
        console.log("SVG explanation:", explanation); // Log SVG explanation
        if (!cancelled) setSvgExplanation(explanation || "No explanation available.");
      } catch (err) {
        console.error("Failed to load SVG explanation:", err);
        if (!cancelled) setSvgExplanation("No explanation available.");
      }
    }

    loadSvg();
    return () => { cancelled = true; };
  }, [selectedSvg]);

  useEffect(() => { if (onSvgChange) onSvgChange(selectedSvg); }, [selectedSvg, onSvgChange]);

  const [animations] = useLiveFeed("animation", "animationupdatemsg", animationKey);

  useEffect(() => {
    if (!svgContent) return;
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

        try { gsap.to(target, gsapConfig); } catch {}
      });
    });

    return () => cancelAnimationFrame(raf);
  }, [animations, svgContent, selectedSvg]);

  // Click handler: use OpenAPI instead of postJson
  useEffect(() => {
    const svgElem = svgContainerRef.current;
    if (!svgElem) return;

    async function handleClick(e) {
      const api = new Api();
      const target = e.target;
      if (!target) return;

      if (target.hasAttribute("command-datapoint")) {
        const command = target.getAttribute("command-datapoint");
        const value = target.getAttribute("command-value") || "";
        if (!window.confirm(`Send command "${command}" with value "${value}"?`)) return;

        try {
          await api.command.sendcommandmsg({
            command_id: "cmd_" + Math.random().toString(36).slice(2),
            datapoint_identifier: command,
            value,
          });
          window.alert("Command sent!");
        } catch (err) {
          window.alert("Error sending command: " + err?.message);
        }
      }

      if (target.hasAttribute("command-communication")) {
        const driver = target.getAttribute("command-communication");
        const value = target.getAttribute("command-value") || "";
        if (!window.confirm(`Send driver command "${driver}" = "${value}"?`)) return;

        try {
          await api.communication.driverconnectcommand({
            driver_name: driver,
            status: value,
          });
          window.alert("Driver command sent!");
        } catch (err) {
          window.alert("Error sending driver command: " + err?.message);
        }
      }
    }

    svgElem.addEventListener("click", handleClick);
    return () => svgElem.removeEventListener("click", handleClick);
  }, [svgContent]);

  return (
    <div>
      <h2>Animated SVGs</h2>

      {!forcedSvg && (
        <select
          value={selectedSvg || ""}
          onChange={(e) => setSelectedSvg(e.target.value)}
          style={{ marginBottom: 8 }}
        >
          {svgList.map((svg) => (
            <option key={svg} value={svg}>{svg}</option>
          ))}
        </select>
      )}

      {forcedSvg && (
        <div style={{ marginBottom: 8, fontWeight: "bold" }}>
          {normalizeSvgName(forcedSvg)}
        </div>
      )}

      <div style={{ display: "flex", gap: 24 }}>
        <div
          id="svgContainer"
          ref={svgContainerRef}
          dangerouslySetInnerHTML={{ __html: svgContent }}
          style={{ minHeight: 300, border: "1px solid #ccc", background: "#fafafa", borderRadius: 6, padding: 8, flex: 1 }}
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
