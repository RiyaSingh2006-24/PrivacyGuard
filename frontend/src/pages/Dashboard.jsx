import { useEffect, useMemo, useState } from "react";
import { Download, RefreshCw, ShieldCheck } from "lucide-react";

export default function Dashboard() {
  const [history, setHistory] = useState([]);
  const [networkInfo, setNetworkInfo] = useState({});
  const [online, setOnline] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [historyResponse, networkResponse] = await Promise.all([
        fetch("/api/history"),
        fetch("/api/network/info"),
      ]);
      if (!historyResponse.ok || !networkResponse.ok) throw new Error("Backend unavailable");
      const historyData = await historyResponse.json();
      const networkData = await networkResponse.json();
      setHistory(historyData.history || []);
      setNetworkInfo(networkData);
      setOnline(true);
    } catch (error) {
      console.error(error);
      setOnline(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const latestNetwork = history.find((item) => item.event_type === "Network Scan");
  const latestIdentity = history.find((item) => item.event_type === "Identity Check");

  const metrics = useMemo(() => {
    const devices = latestNetwork?.devices_found || 0;
    const openServices = latestNetwork?.open_services || 0;
    const riskyServices = latestNetwork?.risky_services || 0;
    const breaches = latestIdentity?.breach_count || 0;
    const networkScore = latestNetwork
      ? Math.max(0, 100 - Math.min(riskyServices * 15, 45) - Math.min(openServices * 2, 10))
      : null;
    const identityScore = latestIdentity?.security_score ?? null;
    let score = 100;
    if (networkScore !== null && identityScore !== null) score = Math.round(networkScore * 0.55 + identityScore * 0.45);
    else if (networkScore !== null) score = networkScore;
    else if (identityScore !== null) score = identityScore;
    const risk = score < 70 ? "High" : score < 90 ? "Medium" : "Low";
    return { devices, openServices, riskyServices, breaches, score, risk };
  }, [latestNetwork, latestIdentity]);

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Your Digital Safety, <span>Simplified.</span></h1>
          <p>Scan. Detect. Understand. Take Control.</p>
        </div>
        <div className="toolbar">
          <button className="btn secondary" onClick={() => window.open("/api/report/security", "_blank")}>
            <Download size={15} /> Download Report
          </button>
          <button className="btn" onClick={load} disabled={loading}>
            <RefreshCw size={15} /> {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      <div className={online ? "online" : "offline"} style={{ marginBottom: 14 }}>
        ● Security Engine {online ? "Online" : "Offline"}
      </div>

      <section className="grid stats">
        <div className="card"><span>Security Score</span><strong className="score">{metrics.score}/100</strong><span className={`badge ${metrics.risk.toLowerCase()}`}>{metrics.risk} Risk</span></div>
        <div className="card"><span>Devices Discovered</span><strong>{metrics.devices}</strong><span>Latest network scan</span></div>
        <div className="card"><span>Risky Services</span><strong>{metrics.riskyServices}</strong><span>Medium / High findings</span></div>
        <div className="card"><span>Identity Breaches</span><strong>{metrics.breaches}</strong><span>Latest exposure check</span></div>
      </section>

      <section className="grid two-col">
        <div className="panel">
          <h2>Network Overview</h2>
          <table className="table">
            <tbody>
              <tr><th>Hostname</th><td>{networkInfo.hostname || "—"}</td></tr>
              <tr><th>Interface</th><td>{networkInfo.interface || "—"}</td></tr>
              <tr><th>Local IP</th><td className="mono">{networkInfo.local_ip || "—"}</td></tr>
              <tr><th>Gateway</th><td className="mono">{networkInfo.gateway || "—"}</td></tr>
              <tr><th>Network</th><td className="mono">{networkInfo.network_range || "—"}</td></tr>
              <tr><th>Open Services</th><td>{metrics.openServices}</td></tr>
            </tbody>
          </table>
        </div>
        <div className="panel">
          <h2>Latest Identity Status</h2>
          {latestIdentity ? (
            <div className="result-list">
              <div className="result-item"><strong>{latestIdentity.status}</strong><p className="muted">Risk: {latestIdentity.risk_level}</p></div>
              <div className="result-item"><span>Security score</span><strong>{latestIdentity.security_score ?? "—"}/100</strong></div>
            </div>
          ) : <p className="muted">No identity check yet.</p>}
        </div>
      </section>

      <section className="panel">
        <h2>Recent Security Activity</h2>
        {history.length === 0 ? <p className="muted">No activity stored yet.</p> : (
          <table className="table">
            <thead><tr><th>Event</th><th>Target</th><th>Risk</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>{history.slice(0, 6).map((item) => (
              <tr key={item.id}><td>{item.event_type}</td><td>{item.target}</td><td>{item.risk_level}</td><td>{item.status}</td><td>{new Date(item.created_at).toLocaleString()}</td></tr>
            ))}</tbody>
          </table>
        )}
      </section>

      <div className="panel small"><ShieldCheck size={14} /> PrivacyGuard score is an advisory heuristic, not a formal security certification.</div>
    </>
  );
}
