import { Navigate, useLocation } from "react-router-dom";
import AppShell from "./AppShell";
import { useAuth } from "../lib/AuthContext";
import { isPublicPath } from "../lib/session";

export default function DeskGate() {
  const location = useLocation();
  const { user, ready } = useAuth();
  if (isPublicPath(location.pathname)) {
    return <AppShell />;
  }
  if (!ready) return null;
  if (!user) {
    const next = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/sign-in?next=${next}`} replace />;
  }
  return <AppShell />;
}
