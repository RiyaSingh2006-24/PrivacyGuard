import { useEffect, useState } from "react";
import { RefreshCw, ShieldCheck } from "lucide-react";

export default function SettingsPage() {
  const [engineOnline, setEngineOnline] = useState(false);
  const [loading, setLoading] = useState(true);
  const [networkInfo, setNetworkInfo] = useState({});

  const monitoredPorts = [
    [21, "FTP", "Medium"],
    [22, "SSH", "Low"],
    [23, "Telnet", "High"],
    [53, "DNS", "Low"],
    [80, "HTTP", "Medium"],
    [443, "HTTPS", "Low"],
    [445, "SMB", "High"],
    [3389, "RDP", "High"],
    [8080, "HTTP Alternate", "Medium"],
  ];

  const load = async () => {
    setLoading(true);
    try {
      const [healthResponse, networkResponse] = await Promise.all([
        fetch("/api/health"),
        fetch("/api/network/info"),
      ]);
      if (!healthResponse.ok || !networkResponse.ok) throw new Error("Backend unavailable");
      const health = await healthResponse.json();
      setNetworkInfo(await networkResponse.json());
      setEngineOnline(health.status === "online");
    } catch (error) {
      console.error(error);
      setEngineOnline(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <>
      <div className="page-header">
        <div>
          <h1>PrivacyGuard <span>Settings</span></h1>
          <p>Review the local security engine, network configuration, and safety controls.</p>
        </div>
        <button className="btn" onClick={load} disabled={loading}>
          <RefreshCw size={15} /> {loading ? "Refreshing..." : "Refresh Status"}
        </button>
      </div>

      <section className="grid stats">
        <div className="card"><span>Security Engine</span><strong style={{ fontSize: 15 }} className={engineOnline ? "online" : "offline"}>{engineOnline ? "PROTECTION ACTIVE" : "OFFLINE"}</strong><span>Local PrivacyGuard Agent</span></div>
        <div className="card"><span>Operating System</span><strong style={{ fontSize: 15 }}>{networkInfo.operating_system || "—"}</strong><span>Current device</span></div>
        <div className="card"><span>Data Storage</span><strong style={{ fontSize: 15 }}>Local SQLite</strong><span>PrivacyGuard history</span></div>
        <div className="card"><span>Protection Mode</span><strong style={{ fontSize: 15 }}>Local Network</strong><span>Authorized networks only</span></div>
      </section>

      <section className="panel">
        <h2>Network Configuration</h2>
        <table className="table">
          <tbody>
            <tr><th>Device Name</th><td>{networkInfo.hostname || "—"}</td></tr>
            <tr><th>Network Interface</th><td>{networkInfo.interface || "—"}</td></tr>
            <tr><th>Local IP</th><td className="mono">{networkInfo.local_ip || "—"}</td></tr>
            <tr><th>Subnet Mask</th><td className="mono">{networkInfo.netmask || "—"}</td></tr>
            <tr><th>Default Gateway</th><td className="mono">{networkInfo.gateway || "—"}</td></tr>
            <tr><th>Protected Network</th><td className="mono">{networkInfo.network_range || "—"}</td></tr>
          </tbody>
        </table>
      </section>

      <section className="grid two-col">
        <div className="panel">
          <h2>Network Scan Protection</h2>
          <div className="result-list">
            <div className="result-item"><strong>Automatic local network detection</strong><p className="muted">PrivacyGuard detects the connected subnet instead of accepting arbitrary internet targets.</p></div>
            <div className="result-item"><strong>Private networks only</strong><p className="muted">Public network ranges are rejected.</p></div>
            <div className="result-item"><strong>Maximum 256 addresses</strong><p className="muted">Scans are intentionally limited to a /24-sized range.</p></div>
            <div className="result-item"><strong>Local-only API</strong><p className="muted">The packaged engine binds to 127.0.0.1.</p></div>
          </div>
        </div>

        <div className="panel">
          <h2>Monitored Services</h2>
          <table className="table">
            <thead><tr><th>Port</th><th>Service</th><th>Classification</th></tr></thead>
            <tbody>
              {monitoredPorts.map(([port, service, risk]) => (
                <tr key={port}><td className="mono">{port}</td><td>{service}</td><td><span className={`badge ${risk.toLowerCase()}`}>{risk}</span></td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="panel small"><ShieldCheck size={14} /> Authorized Use Only: PrivacyGuard is intended for networks and systems you own or have explicit permission to assess.</div>
    </>
  );
}
