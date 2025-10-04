import React, { createContext, useContext, useState } from "react";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("jwt_token"));
  const [user, setUser] = useState(null);

  function login(token, user) {
    setToken(token);
    setUser(user);
    localStorage.setItem("jwt_token", token);
  }
  function logout() {
    setToken(null);
    setUser(null);
    localStorage.removeItem("jwt_token");
  }

  return (
    <AuthContext.Provider value={{ token, user, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}