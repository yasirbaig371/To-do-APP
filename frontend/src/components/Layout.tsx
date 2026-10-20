import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../auth/AuthContext";

export function AppLayout() {
  const { user, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [logoutError, setLogoutError] = useState("");
  const navigate = useNavigate();

  async function handleLogout() {
    setLogoutError("");
    try {
      await signOut();
      navigate("/login", { replace: true });
    } catch {
      setLogoutError("Could not contact the API to log out. Try again.");
    }
  }

  return (
    <div className="app-frame">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <NavLink className="brand" to="/">
          <span className="brand-mark" aria-hidden="true">d.</span>
          <span>daymark<span className="brand-period">.</span></span>
        </NavLink>
        <p className="nav-label">WORKSPACE</p>
        <nav className="primary-nav" aria-label="Main navigation">
          {user?.role === "admin" ? (
            <>
              <NavLink to="/admin" end onClick={() => setMenuOpen(false)}>
                <span className="nav-icon">▦</span> Overview
              </NavLink>
              <NavLink to="/admin/users" onClick={() => setMenuOpen(false)}>
                <span className="nav-icon">♙</span> People
              </NavLink>
              <NavLink to="/chat" onClick={() => setMenuOpen(false)}>
                <span className="nav-icon">✦</span> Assistant
              </NavLink>
            </>
          ) : (
            <>
              <NavLink to="/" end onClick={() => setMenuOpen(false)}>
                <span className="nav-icon">⌂</span> Overview
              </NavLink>
              <NavLink to="/tasks" onClick={() => setMenuOpen(false)}>
                <span className="nav-icon">☷</span> My tasks
              </NavLink>
            </>
          )}
          <NavLink to="/chat" onClick={() => setMenuOpen(false)}>
            <span className="nav-icon">✦</span> Assistant
          </NavLink>
          <NavLink to="/profile" onClick={() => setMenuOpen(false)}>
            <span className="nav-icon">◉</span> Profile
          </NavLink>
        </nav>
        <div className="sidebar-bottom">
          <div className="profile-mini">
            <span className="avatar">{user?.full_name.slice(0, 1).toUpperCase()}</span>
            <span className="profile-mini-copy">
              <strong>{user?.full_name}</strong>
              <small>{user?.role === "admin" ? "Administrator" : "Member"}</small>
            </span>
          </div>
          <button className="logout-button" type="button" onClick={handleLogout}>
            <span aria-hidden="true">↪</span> Sign out
          </button>
          {logoutError && <p className="sidebar-error" role="alert">{logoutError}</p>}
        </div>
      </aside>
      {menuOpen && (
        <button
          className="sidebar-backdrop"
          aria-label="Close navigation menu"
          onClick={() => setMenuOpen(false)}
        />
      )}
      <main className="main-panel">
        <header className="mobile-header">
          <NavLink className="brand" to="/">
            <span className="brand-mark" aria-hidden="true">d.</span>
            <span>daymark<span className="brand-period">.</span></span>
          </NavLink>
          <button
            className="menu-toggle"
            type="button"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? "×" : "☰"}
          </button>
        </header>
        <Outlet />
      </main>
    </div>
  );
}
