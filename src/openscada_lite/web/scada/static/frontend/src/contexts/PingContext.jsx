import React, { createContext, useContext, useEffect, useState } from "react";
import { Api } from "generatedApi";
const PingContext = createContext({ isConnected: true, serverTimestamp: "" });

export function PingProvider({ children }) {
  const [isConnected, setIsConnected] = useState(true);
  const [serverTimestamp, setServerTimestamp] = useState("");
  const api = new Api();

  useEffect(() => {
    let mounted = true;
    const tick = async () => {
      try {
        const res = await api.frontend.ping();
        const data = res?.data || {};
        if (!mounted) return;
        setIsConnected(!!res?.ok);
        setServerTimestamp(data?.timestamp || "");
      } catch (e) {
        if (!mounted) return;
        setIsConnected(false);
        setServerTimestamp("");
      }
    };

    // initial ping and interval
    tick();
    const interval = setInterval(tick, 5000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <PingContext.Provider value={{ isConnected, serverTimestamp }}>
      {children}
    </PingContext.Provider>
  );
}

export function usePing() {
  return useContext(PingContext);
}
