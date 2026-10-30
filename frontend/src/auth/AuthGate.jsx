import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext.jsx";
import { ErrorState, LoadingState } from "../components/Ui.jsx";

export default function AuthGate({ children }) {
  const { status, authError, refresh } = useAuth();
  const location = useLocation();

  if (status === "loading") return <LoadingState label="Checking your account..." />;
  if (status === "error") {
    return <main className="auth-service-error"><ErrorState message={authError} onRetry={refresh} /></main>;
  }
  if (status !== "authenticated") {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return children;
}
