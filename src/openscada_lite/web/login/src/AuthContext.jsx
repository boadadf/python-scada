import React, { createContext, useContext, useState } from "react";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  function login(userInfo) {
    setUser(userInfo);
    setIsAuthenticated(true);
  }

  function logout() {
    setUser(null);
    setIsAuthenticated(false);

    // Optional: call backend logout to clear cookie
    fetch("/security/logout", {
      method: "POST",
      credentials: "include",
    });
  }

  return (
    <AuthContext.Provider
      value={{ user, login, logout, isAuthenticated }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
