import React, { useEffect, useRef, useState } from "react";
import { gsap } from "gsap";
import { TextPlugin } from "gsap/TextPlugin";
import { useLiveFeed } from "../livefeed/useLiveFeed";

gsap.registerPlugin(TextPlugin);

function animationKey(msg) {
  // Compose a unique key for each animation message
  return (msg.svg_name || "") + "_" + (msg.element_id || "");
}

export default function ImageView({ selectedSvgProp, onSvgChange }) {
  const [svgList, setSvgList] = useState([]);
  const [selectedSvg, setSelectedSvg] = useState(selectedSvgProp || null);
  const [svgContent, setSvgContent] = useState("");
  const svgContainerRef = useRef(null);

  // Use the live feed for animation messages
  const [animations] = useLiveFeed("animation", "animationupdatemsg", animationKey);

  // For commands to datapoint
  const [, , postCommand] = useLiveFeed("command", "sendcommandmsg", () => {}, "sendcommandmsg");
  // For commands to communication
  const [, , postCommunication] = useLiveFeed("communication", "driverconnectcommand", () => {}, "driverconnectcommand");

  useEffect(() => {
    if (selectedSvgProp && selectedSvgProp !== selectedSvg) {
      setSelectedSvg(selectedSvgProp);
    }
  }, [selectedSvgProp]);

  useEffect(() => {
    if (onSvgChange) onSvgChange(selectedSvg);
  }, [selectedSvg]);

  useEffect(() => {
    fetch("/animation_svgs")
      .then(r => r.json())
      .then(svgs => {
        setSvgList(svgs);
        if (!selectedSvg && svgs.length) setSelectedSvg(svgs[0]);
      });
  }, []);

  useEffect(() => {
    if (!selectedSvg) return;
    fetch(`/svg/${selectedSvg}`)
      .then(r => r.text())
      .then(svg => setSvgContent(svg));
  }, [selectedSvg]);

  // Apply animation updates from live feed
  useEffect(() => {
    if (!svgContent) return;
    const svgElem = svgContainerRef.current;
    if (!svgElem) return;

    Object.values(animations).forEach(msg => {
      if (!msg || msg.svg_name !== selectedSvg) return;
      const elem = svgElem.querySelector(`#${msg.element_id}`);
      if (!elem || !msg.config) return;

      const gsapConfig = { duration: msg.config.duration || 0.5 };
      if (msg.config.attr) gsapConfig.attr = msg.config.attr;
      if (msg.config.text) gsapConfig.text = msg.config.text;

      gsap.to(elem, gsapConfig);
    });
  }, [animations, svgContent, selectedSvg]);

  // Handle SVG click commands using unified postJson
  useEffect(() => {
    const svgElem = svgContainerRef.current;
    if (!svgElem) return;

    function handleClick(e) {
      const target = e.target;

      if (target && target.hasAttribute("command-datapoint")) {
        const command = target.getAttribute("command-datapoint");
        const value = target.getAttribute("command-value") || "";
        if (window.confirm(`Send command "${command}" with value "${value}"?`)) {
          const payload = {
            command_id: command,
            datapoint_identifier: command,
            value: value,
          };
          postCommand(payload)
            .then(data => alert(data.reason || "Command sent!"))
            .catch(() => alert("Error sending command"));
        }
      }

      if (target && target.hasAttribute("command-communication")) {
        const driver = target.getAttribute("command-communication");
        const value = target.getAttribute("command-value") || "";
        if (window.confirm(`Send command "${driver}" with value "${value}"?`)) {
          postCommunication({
            driver_name: driver,
            status: value
          })
            .then(data => alert(data.reason || "Command sent!"))
            .catch(err => alert("Error sending command: " + err));
        }
      }
    }

    svgElem.addEventListener("click", handleClick);
    return () => svgElem.removeEventListener("click", handleClick);
  }, [svgContent, postCommand, postCommunication]);

  return (
    <div>
      <h2>Animated SVGs</h2>
      <select
        value={selectedSvg || ""}
        onChange={e => setSelectedSvg(e.target.value)}
        style={{ marginBottom: 8 }}
      >
        {svgList.map(svg => (
          <option key={svg} value={svg}>{svg}</option>
        ))}
      </select>
      <div
        id="svgContainer"
        ref={svgContainerRef}
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: svgContent }}
        style={{ minHeight: 300, border: "1px solid #ccc", background: "#fafafa" }}
      />
    </div>
  );
}