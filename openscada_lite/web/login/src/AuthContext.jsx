import React, { createContext, useContext, useState } from "react";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("jwt_token"));
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem("user_info");
    return storedUser ? JSON.parse(storedUser) : null;
  });

  function login(token, userInfo) {
    setToken(token);
    setUser(userInfo);
    localStorage.setItem("jwt_token", token);
    localStorage.setItem("user_info", JSON.stringify(userInfo));
  }
  
  function logout() {
    setToken(null);
    setUser(null);
    localStorage.removeItem("jwt_token");
    localStorage.removeItem("user_info");
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