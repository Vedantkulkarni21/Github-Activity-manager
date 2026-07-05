import { useEffect, useState } from "react";
import { Plus, Trash2, Globe } from "lucide-react";
import { api } from "../api/client";

export default function Repos() {
  const [connected, setConnected] = useState(null);
  const [available, setAvailable] = useState(null);
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const loadAll = async () => {
    try {
      const [c, a] = await Promise.all([api.connectedRepos(), api.availableRepos()]);
      setConnected(c);
      setAvailable(a);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const connectable = (available || []).filter((r) => !r.already_connected);

  const handleConnect = async () => {
    if (!selected) return;
    setBusy(true);
    setError(null);
    try {
      await api.connectRepo(selected);
      setSelected("");
      await loadAll();
    } catch (err) {
      setError(err.message || "Couldn't connect that repo");
    } finally {
      setBusy(false);
    }
  };

  const handleDisconnect = async (id) => {
    setBusy(true);
    try {
      await api.disconnectRepo(id);
      await loadAll();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Repositories</h1>
          <p className="page-subtitle">Connecting a repo installs a webhook so the bot can see its activity.</p>
        </div>
      </div>

      {error && <div className="card" style={{ color: "var(--signal-fail)", marginBottom: 14 }}>{error}</div>}

      <div className="card" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 10 }}>
          <select
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
            style={{
              flex: 1, background: "var(--bg-raised)", border: "1px solid var(--border-strong)",
              borderRadius: "var(--radius-sm)", color: "var(--text-primary)", padding: "9px 11px", fontSize: 13.5,
            }}
          >
            <option value="">
              {available === null ? "Loading your repos…" : connectable.length === 0 ? "No repos available to connect" : "Select a repo to connect"}
            </option>
            {connectable.map((r) => (
              <option key={r.full_name} value={r.full_name}>
                {r.full_name} {r.private ? "(private)" : ""}
              </option>
            ))}
          </select>
          <button className="btn btn-primary" disabled={!selected || busy} onClick={handleConnect}>
            <Plus size={15} /> Connect
          </button>
        </div>
      </div>

      {connected === null && <div className="card">Loading connected repos…</div>}

      {connected && connected.length === 0 && (
        <div className="empty-state">
          <h3>Nothing connected yet</h3>
          <p>Pick a repo above to start receiving its events.</p>
        </div>
      )}

      {connected && connected.length > 0 && (
        <div className="card">
          {connected.map((r) => (
            <div className="repo-row" key={r.id}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Globe size={14} color="var(--text-muted)" />
                <span className="repo-name">{r.full_name}</span>
              </div>
              <button className="btn btn-sm btn-danger-ghost" disabled={busy} onClick={() => handleDisconnect(r.id)}>
                <Trash2 size={13} /> Disconnect
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
