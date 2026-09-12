import { useState } from "react";
import { Search, ShieldCheck, TriangleAlert } from "lucide-react";

export default function Identity() {
  const [email, setEmail] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const checkIdentity = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await fetch("/api/identity/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await response.json();
      if (!response.ok || data.status !== "success") {
        throw new Error(data.message || "Identity check failed.");
      }
      setResult(data);
    } catch (err) {
      console.error(err);
      setError(err.message || "Unable to complete identity check.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Identity <span>Exposure</span></h1>
          <p>Check whether an email address appears in known breach intelligence.</p>
        </div>
      </div>

      <section className="panel">
        <h2>Check Exposure</h2>
        <div className="form-row">
          <input
            className="input"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            onKeyDown={(event) => event.key === "Enter" && checkIdentity()}
          />
          <button className="btn" onClick={checkIdentity} disabled={loading || !email.trim()}>
            <Search size={15} /> {loading ? "Checking..." : "Check Exposure"}
          </button>
        </div>
        <p className="muted small">The submitted email is sent to the configured external breach-intelligence provider for lookup. Stored local history masks the address.</p>
      </section>

      {error && <div className="alert"><TriangleAlert size={15} /> {error}</div>}

      {result && (
        <>
          <section className="grid stats">
            <div className="card"><span>Security Score</span><strong className="score">{result.security_score}/100</strong></div>
            <div className="card"><span>Known Breaches</span><strong>{result.breach_count}</strong></div>
            <div className="card"><span>Risk Level</span><strong>{result.risk_level}</strong></div>
            <div className="card"><span>Status</span><strong>{result.breached ? "Exposed" : "Clear"}</strong></div>
          </section>

          <section className="panel">
            <h2>{result.breached ? "Breach Details" : "No Known Breach Returned"}</h2>
            {!result.breached ? (
              <div className="result-item"><ShieldCheck size={18} /> <strong>No known breach was returned by the current provider.</strong></div>
            ) : (
              <div className="result-list">
                {result.breaches.map((breach, index) => (
                  <div className="result-item" key={`${breach.name}-${index}`}>
                    <strong>{breach.name}</strong>
                    <p className="muted">{breach.domain} · {breach.year} · {breach.industry}</p>
                    <p><strong>Exposed data:</strong> {breach.exposed_data?.join(", ") || "Unknown"}</p>
                    <p><strong>Password risk:</strong> {breach.password_risk}</p>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="panel">
            <h2>Recommended Actions</h2>
            <div className="result-list">
              {result.recommendations.map((item, index) => (
                <div className="result-item" key={index}>{item}</div>
              ))}
            </div>
          </section>
        </>
      )}
    </>
  );
}
