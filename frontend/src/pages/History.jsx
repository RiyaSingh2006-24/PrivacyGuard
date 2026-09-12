import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [filter, setFilter] = useState("All");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/history");
      const data = await response.json();
      setHistory(data.history || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    if (filter === "Network") return history.filter((item) => item.event_type === "Network Scan");
    if (filter === "Identity") return history.filter((item) => item.event_type === "Identity Check");
    return history;
  }, [history, filter]);

  const networkCount = history.filter((item) => item.event_type === "Network Scan").length;
  const identityCount = history.filter((item) => item.event_type === "Identity Check").length;
  const riskCount = history.filter((item) => item.risk_level === "High" || item.risk_level === "Medium").length;

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Security <span>History</span></h1>
          <p>Review local network scans and masked identity checks stored by PrivacyGuard.</p>
        </div>
        <button className="btn" onClick={load} disabled={loading}>
          <RefreshCw size={15} /> {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <section className="grid stats">
        <div className="card"><span>Total Activities</span><strong>{history.length}</strong></div>
        <div className="card"><span>Network Scans</span><strong>{networkCount}</strong></div>
        <div className="card"><span>Identity Checks</span><strong>{identityCount}</strong></div>
        <div className="card"><span>Risk Events</span><strong>{riskCount}</strong></div>
      </section>

      <section className="panel">
        <div className="toolbar" style={{ marginBottom: 12 }}>
          {["All", "Network", "Identity"].map((item) => (
            <button
              key={item}
              className={filter === item ? "btn" : "btn secondary"}
              onClick={() => setFilter(item)}
            >
              {item}
            </button>
          ))}
        </div>

        {filtered.length === 0 ? <p className="muted">No matching security activity.</p> : (
          <table className="table">
            <thead><tr><th>Event</th><th>Target</th><th>Devices</th><th>Open Services</th><th>Breaches</th><th>Risk</th><th>Status</th><th>Date</th></tr></thead>
            <tbody>
              {filtered.map((item) => (
                <tr key={item.id}>
                  <td>{item.event_type}</td>
                  <td className="mono">{item.target}</td>
                  <td>{item.devices_found || 0}</td>
                  <td>{item.open_services || 0}</td>
                  <td>{item.breach_count || 0}</td>
                  <td><span className={`badge ${item.risk_level?.toLowerCase()}`}>{item.risk_level}</span></td>
                  <td>{item.status}</td>
                  <td>{new Date(item.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <div className="panel small">History is stored locally in SQLite. Identity targets are masked before being written to history.</div>
    </>
  );
}
