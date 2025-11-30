import React, { createContext, useContext, useState } from "react";

const UserActionContext = createContext();

export function UserActionProvider({ children }) {
  const [payload, setPayload] = useState(null);
  return (
    <UserActionContext.Provider value={{ payload, setPayload }}>
      {children}
    </UserActionContext.Provider>
  );
}

export function useUserAction() {
  return useContext(UserActionContext);
}