import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Loading } from "./Shared";

export function ProtectedRoute({ adminOnly = false }: { adminOnly?: boolean }) {
  const { user, ready } = useAuth();
  const location = useLocation();
  if (!ready) return <Loading />;
  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (adminOnly && user.role !== "admin") {
    return <Navigate to="/" replace />;
  }
  if (!adminOnly && user.role === "admin" && location.pathname === "/") {
    return <Navigate to="/admin" replace />;
  }
  return <Outlet />;
}
