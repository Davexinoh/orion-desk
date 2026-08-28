import { NavLink, Outlet } from "react-router-dom";

const desktopNav = [
  { to: "/desk", label: "Missions", end: true },
  { to: "/desk/approvals", label: "Approvals" },
  { to: "/desk/receipts", label: "Receipts" },
  { to: "/desk/memory", label: "Memory" },
  { to: "/desk/settings", label: "Settings" },
];

const mobileNav = desktopNav.filter((l) => l.label !== "Settings");

export default function DeskShell() {
  return (
    <div className="od-app-shell">
      <header className="od-top">
        <div className="od-top-inner">
          <NavLink to="/" className="wordmark">
            Orion <em>Desk</em>
          </NavLink>
          <nav className="od-nav">
            {desktopNav.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.end}>
                {l.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="od-main">
        <Outlet />
      </main>

      <nav className="od-mobile-nav" aria-label="Desk">
        {mobileNav.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end}>
            {l.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
