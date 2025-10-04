import React, { useEffect, useRef, useState } from "react";

// Make sure to install gsap: npm install gsap
import { gsap } from "gsap";
import { TextPlugin } from "gsap/TextPlugin";

// Register GSAP TextPlugin
gsap.registerPlugin(TextPlugin);

export default function ImageView() {
  const [svgList, setSvgList] = useState([]);
  const [selectedSvg, setSelectedSvg] = useState("");
  const [svgContent, setSvgContent] = useState("");
  const svgContainerRef = useRef(null);
  const socketRef = useRef(null);

  // Fetch SVG list on mount
  useEffect(() => {
    fetch("/animation_svgs")
      .then(r => r.json())
      .then(svgs => {
        setSvgList(svgs);
        if (svgs.length) setSelectedSvg(svgs[0]);
      });
  }, []);

  // Fetch SVG content when selectedSvg changes
  useEffect(() => {
    if (!selectedSvg) return;
    fetch(`/svg/${selectedSvg}`)
      .then(r => r.text())
      .then(svg => setSvgContent(svg));
  }, [selectedSvg]);

  // Setup Socket.IO and animation logic
  useEffect(() => {
    // Dynamically load socket.io if not present
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
      socket.on("animation_animationupdatemsg", msg => {
        if (msg.svg_name !== selectedSvg) return;
        // Wait for SVG to be rendered
        setTimeout(() => {
          const svgElem = svgContainerRef.current;
          if (!svgElem) return;
          const elem = svgElem.querySelector(`#${msg.element_id}`);
          if (!elem || !msg.config) return;
          const gsapConfig = { duration: msg.config.duration || 0.5 };
          if (msg.config.attr) gsapConfig.attr = msg.config.attr;
          if (msg.config.text) gsapConfig.text = msg.config.text;
          gsap.to(elem, gsapConfig);
        }, 0);
      });
    }
  }, [selectedSvg]);

  // Handle command clicks in SVG
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
            value: value
          };
          fetch("/command_send_sendcommandmsg", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          })
            .then(resp => resp.json())
            .then(data => alert(data.reason || "Command sent!"))
            .catch(() => alert("Error sending command"));
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
        value={selectedSvg}
        onChange={e => setSelectedSvg(e.target.value)}
        style={{ marginBottom: 8 }}
      >
        {svgList.map(name => (
          <option key={name} value={name}>{name}</option>
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