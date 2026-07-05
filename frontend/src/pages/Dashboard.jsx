import { useEffect, useState, useCallback } from "react";
import { RefreshCw } from "lucide-react";
import { api } from "../api/client";
import PipelineRow from "../components/PipelineRow";

const POLL_MS = 8000;

export default function Dashboard() {
  const [events, setEvents] = useState(null);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  const load = useCallback(async () => {
    try {
      const data = await api.listEvents();
      setEvents(data);
      setError(null);
    } catch (err) {
      setError(err.message || "Couldn't load events");
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, POLL_MS);
    return () => clearInterval(interval);
  }, [load]);

  const handleRetry = async (id) => {
    try {
      await api.retryEvent(id);
      setToast("Retry scheduled");
      setTimeout(() => setToast(null), 2500);
      setTimeout(load, 1500);
    } catch (err) {
      setToast(err.message || "Retry failed");
      setTimeout(() => setToast(null), 2500);
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Event log</h1>
          <p className="page-subtitle">Every webhook received, the rule it matched, and what the bot did about it.</p>
        </div>
        <button className="btn btn-sm" onClick={load}>
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      {error && <div className="card" style={{ color: "var(--signal-fail)" }}>{error}</div>}

      {events === null && !error && <div className="card">Loading events…</div>}

      {events && events.length === 0 && (
        <div className="empty-state">
          <h3>No events yet</h3>
          <p>Connect a repository and open an issue or PR on it — it'll show up here within seconds.</p>
        </div>
      )}

      {events && events.length > 0 && (
        <div className="card" style={{ padding: "6px 16px" }}>
          {events.map((e) => (
            <PipelineRow key={e.id} event={e} onRetry={handleRetry} />
          ))}
        </div>
      )}

      {toast && <div className="toast">{toast}</div>}
    </>
  );
}
