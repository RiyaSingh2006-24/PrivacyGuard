import {
  LayoutDashboard,
  Wifi,
  UserRoundSearch,
  History as HistoryIcon,
  Settings as SettingsIcon,
  ShieldCheck,
} from "lucide-react";
import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import Network from "./pages/Network.jsx";
import Identity from "./pages/Identity.jsx";
import HistoryPage from "./pages/History.jsx";
import SettingsPage from "./pages/Settings.jsx";
import "./App.css";

function App() {
  const items = [
    ["/", "Dashboard", LayoutDashboard, true],
    ["/network", "Network", Wifi],
    ["/identity", "Identity", UserRoundSearch],
    ["/history", "History", HistoryIcon],
    ["/settings", "Settings", SettingsIcon],
  ];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><ShieldCheck size={24} /></div>
          <div>
            <h2>PrivacyGuard</h2>
            <p>See More. Stay Safer.</p>
          </div>
        </div>

        <nav className="menu">
          {items.map(([to, label, Icon, end]) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => isActive ? "menu-item active" : "menu-item"}
            >
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="side-card">
          <strong>PrivacyGuard Engine</strong>
          <p>Local network and identity protection.</p>
          <span>v2.1.0 · Scan · Detect · Protect</span>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <strong>PrivacyGuard</strong>
          <span className="online">● Local Protection</span>
        </header>

        <section className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/network" element={<Network />} />
            <Route path="/identity" element={<Identity />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </section>
      </main>
    </div>
  );
}

export default App;
