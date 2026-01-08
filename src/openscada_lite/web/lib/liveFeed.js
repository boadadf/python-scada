import { useEffect, useRef, useState } from "react";

// Live feed hook: only for real-time updates
export function useLiveFeed(endpoint, updateMsgType, getKey) {
  const [items, setItems] = useState({});
  const socketRef = useRef(null);

  useEffect(() => {
    let socket;
    function setupSocket() {
      socket = globalThis.io({
        path: "/socket.io/",
        transports: ["websocket", "polling"],
      });


      socketRef.current = socket;

      socket.on("connect", () => {
        socket.emit(`${endpoint}_subscribe_live_feed`);
      });

      socket.on(`${endpoint}_initial_state`, (list) => {
        console.log(`[${endpoint}] Received initial state with ${Array.isArray(list) ? list.length : 0} items.`); 
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

    if (globalThis.io) {
      setupSocket();
      return () => socketRef.current?.disconnect();
    } else {
      const script = document.createElement("script");
      script.src = "https://cdn.socket.io/4.7.5/socket.io.min.js";
      script.onload = setupSocket;
      document.body.appendChild(script);
      return () => {
        if (socketRef.current) socketRef.current.disconnect();
        script.remove();
      };
    }
  }, [endpoint, updateMsgType, getKey]);

  return [items, setItems];
}
