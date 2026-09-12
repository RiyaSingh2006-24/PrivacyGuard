import { useEffect, useState } from "react";
import { RefreshCw, ShieldCheck, TriangleAlert } from "lucide-react";

export default function Network() {
  const [networkInfo, setNetworkInfo] = useState({});
  const [scanData, setScanData] = useState(null);
  const [knownDevices, setKnownDevices] = useState([]);
  const [trustedIds, setTrustedIds] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");
  const [trustLoading, setTrustLoading] = useState(null);

  const loadNetworkInfo = async () => {
    try {
      const response = await fetch("/api/network/info");
      if (!response.ok) throw new Error("PrivacyGuard engine unavailable");
      setNetworkInfo(await response.json());
    } catch (err) {
      console.error(err);
      setError("Unable to connect to the PrivacyGuard security engine.");
    }
  };

  const loadKnownDevices = async () => {
    try {
      const response = await fetch("/api/network/devices");
      const data = await response.json();
      if (data.status === "success") setKnownDevices(data.devices || []);
    } catch (err) {
      console.error(err);
    }
  };

  const loadTrustStatus = async () => {
    try {
      const response = await fetch("/api/network/trust-status");
      const data = await response.json();
      if (data.status === "success") setTrustedIds(data.trusted_ids || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadNetworkInfo();
    loadKnownDevices();
    loadTrustStatus();
  }, []);

  const runNetworkScan = async () => {
    setScanning(true);
    setError("");
    try {
      const response = await fetch("/api/network/scan");
      const data = await response.json();
      if (!response.ok || data.status !== "success") {
        throw new Error(data.message || "Network scan failed.");
      }
      setScanData(data);
      await Promise.all([loadKnownDevices(), loadTrustStatus()]);
    } catch (err) {
      console.error(err);
      setError(err.message || "An unexpected scanning error occurred.");
    } finally {
      setScanning(false);
    }
  };

  const findKnownDevice = (device) => {
    if (device.mac) {
      const byMac = knownDevices.find(
        (known) => known.mac && known.mac.toUpperCase() === device.mac.toUpperCase()
      );
      if (byMac) return byMac;
    }
    return knownDevices.find((known) => known.ip === device.ip);
  };

  const toggleTrust = async (device) => {
    const known = findKnownDevice(device);
    if (!known) return;
    const trusted = trustedIds.includes(known.id);
    setTrustLoading(known.id);
    try {
      const response = await fetch(`/api/network/devices/${known.id}/trust`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ trusted: !trusted }),
      });
      if (!response.ok) throw new Error("Unable to update device trust.");
      await loadTrustStatus();
    } catch (err) {
      setError(err.message);
    } finally {
      setTrustLoading(null);
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Network <span>Security</span></h1>
          <p>Discover devices, inspect common exposed services, and recognize unfamiliar devices.</p>
        </div>
        <button className="btn" onClick={runNetworkScan} disabled={scanning}>
          <RefreshCw size={15} /> {scanning ? "Scanning..." : "Run Network Scan"}
        </button>
      </div>

      {error && <div className="alert"><TriangleAlert size={15} /> {error}</div>}

      {scanData?.new_device_count > 0 && (
        <div className="alert">
          <strong>{scanData.new_device_count} new device{scanData.new_device_count > 1 ? "s" : ""} detected.</strong>
          <div className="small">Review each device and mark it trusted only if you recognize it.</div>
        </div>
      )}

      <section className="grid stats">
        <div className="card"><span>Protected Network</span><strong className="mono" style={{ fontSize: 16 }}>{networkInfo.network_range || "—"}</strong></div>
        <div className="card"><span>Gateway</span><strong className="mono" style={{ fontSize: 16 }}>{networkInfo.gateway || "—"}</strong></div>
        <div className="card"><span>Devices Online</span><strong>{scanData?.devices_found ?? "—"}</strong></div>
        <div className="card"><span>Remembered Devices</span><strong>{knownDevices.length}</strong></div>
      </section>

      <section className="panel">
        <h2>Discovered Devices</h2>
        {!scanData ? <p className="muted">Run a scan to discover devices on your local network.</p> : (
          <table className="table">
            <thead><tr><th>Device</th><th>IP</th><th>MAC</th><th>Ports</th><th>Risk</th><th>Trust</th></tr></thead>
            <tbody>
              {scanData.devices.map((device) => {
                const known = findKnownDevice(device);
                const trusted = known ? trustedIds.includes(known.id) : false;
                return (
                  <tr key={device.ip}>
                    <td><strong>{device.name}</strong><div className="muted small">{device.type}{device.is_new ? " · NEW" : ""}</div></td>
                    <td className="mono">{device.ip}</td>
                    <td className="mono">{device.mac || "Not available"}</td>
                    <td>{device.open_ports?.length ? device.open_ports.join(", ") : "None"}</td>
                    <td><span className={`badge ${device.risk?.toLowerCase()}`}>{device.risk}</span></td>
                    <td>
                      <button
                        className={trusted ? "btn good" : "btn secondary"}
                        disabled={!known || trustLoading === known?.id}
                        onClick={() => toggleTrust(device)}
                      >
                        <ShieldCheck size={13} /> {trustLoading === known?.id ? "Saving..." : trusted ? "Trusted" : "Trust"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>

      {scanData && (
        <section className="panel">
          <h2>Service Findings</h2>
          {scanData.findings.length === 0 ? <p className="muted">No monitored common services detected.</p> : (
            <div className="result-list">
              {scanData.findings.map((finding, index) => (
                <div className="result-item" key={`${finding.ip}-${finding.port}-${index}`}>
                  <strong>{finding.service} · Port {finding.port}</strong>
                  <p className="muted">{finding.device} · {finding.ip}</p>
                  <p>{finding.recommendation}</p>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      <div className="panel small">
        <ShieldCheck size={14} /> Trusted means recognized by the user; it does not prove the device is secure. Scan only networks you own or are authorized to assess.
      </div>
    </>
  );
}
