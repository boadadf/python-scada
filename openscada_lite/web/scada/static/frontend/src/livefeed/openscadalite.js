import { useEffect, useRef, useState } from "react";

// Live feed hook: only for real-time updates
export function useLiveFeed(endpoint, updateMsgType, getKey) {
  const [items, setItems] = useState({});
  const socketRef = useRef(null);

  useEffect(() => {
    let socket;
    function setupSocket() {
      socket = window.io();
      socketRef.current = socket;

      socket.on("connect", () => {
        socket.emit(`${endpoint}_subscribe_live_feed`);
      });

      socket.on(`${endpoint}_initial_state`, (list) => {
        const arr = Array.isArray(list) ? list : list ? [list] : [];
        const map = {};
        arr.forEach(item => {
          const key = getKey(item);
          if (key) map[key] = item;
        });
        setItems(map);
      });

      socket.on(`${endpoint}_${updateMsgType.toLowerCase()}`, (itemOrList) => {
        const arr = Array.isArray(itemOrList) ? itemOrList : [itemOrList];
        setItems(prev => {
          const copy = { ...prev };
          arr.forEach(item => {
            const key = getKey(item);
            if (key) copy[key] = item;
          });
          return copy;
        });
      });
    }

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
      return () => socketRef.current?.disconnect();
    }
  }, [endpoint, updateMsgType, getKey]);

  return [items, setItems];
}

// POST-only helper (no socket)
export async function postJson(endpoint, postType, data, extraHeaders = {}) {
  const url = `/${endpoint}_send_${postType}`;
  const headers = {
    "Content-Type": "application/json",
    "X-User": localStorage.getItem("username") || "",
    ...extraHeaders,
  };
  const response = await fetch(url, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    let msg = "Unknown error";
    try {
      const result = await response.json();
      msg = result.reason || JSON.stringify(result);
    } catch {}
    throw new Error(msg);
  }
  return response.json();
}