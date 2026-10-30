import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../services/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState("loading");
  const [authError, setAuthError] = useState("");

  const refresh = useCallback(async () => {
    setStatus("loading");
    setAuthError("");
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
      setStatus("authenticated");
    } catch (error) {
      setUser(null);
      if (error.response?.status === 401) {
        setStatus("unauthenticated");
      } else {
        setStatus("error");
        setAuthError(error.response?.data?.detail || "The account service is unavailable.");
      }
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const signIn = useCallback(async (credentials) => {
    const { data } = await api.post("/auth/login", credentials);
    setUser(data);
    setStatus("authenticated");
    setAuthError("");
    return data;
  }, []);

  const signOut = useCallback(async () => {
    await api.post("/auth/logout");
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const value = useMemo(
    () => ({ user, setUser, status, authError, refresh, signIn, signOut }),
    [user, status, authError, refresh, signIn, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider.");
  return context;
}
