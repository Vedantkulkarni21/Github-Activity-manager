import { useEffect, useState } from "react";
import { Plus, Trash2, Tag, MessageSquare, Slack } from "lucide-react";
import { api } from "../api/client";

const EMPTY_FORM = {
  event_type: "issues",
  match_field: "title",
  match_type: "contains",
  match_value: "",
  action_add_label: "",
  action_comment_template: "",
  action_slack_notify: true,
};

export default function Rules() {
  const [rules, setRules] = useState(null);
  const [repos, setRepos] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const [r, c] = await Promise.all([api.listRules(), api.connectedRepos()]);
      setRules(r);
      setRepos(c);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const update = (field, value) => setForm((f) => ({ ...f, [field]: value }));

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.match_value.trim()) {
      setError("Add a keyword to match on");
      return;
    }
    if (!form.action_add_label.trim() && !form.action_comment_template.trim() && !form.action_slack_notify) {
      setError("Pick at least one action for this rule");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const payload = {
        ...form,
        repo_id: form.repo_id || null,
        action_add_label: form.action_add_label.trim() || null,
        action_comment_template: form.action_comment_template.trim() || null,
      };
      await api.createRule(payload);
      setForm(EMPTY_FORM);
      await load();
    } catch (err) {
      setError(err.message || "Couldn't create rule");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.deleteRule(id);
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const repoName = (id) => (id ? repos.find((r) => r.id === id)?.full_name || "unknown repo" : "all your repos");

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Rules</h1>
          <p className="page-subtitle">Match on keywords and decide what the bot does when they show up.</p>
        </div>
      </div>

      {error && <div className="card" style={{ color: "var(--signal-fail)", marginBottom: 14 }}>{error}</div>}

      <form className="card form-grid" onSubmit={handleCreate} style={{ marginBottom: 20 }}>
        <div className="form-row">
          <div className="field">
            <label>Applies to</label>
            <select value={form.repo_id || ""} onChange={(e) => update("repo_id", e.target.value)}>
              <option value="">All connected repos</option>
              {repos.map((r) => (
                <option key={r.id} value={r.id}>{r.full_name}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>When a</label>
            <select value={form.event_type} onChange={(e) => update("event_type", e.target.value)}>
              <option value="issues">Issue</option>
              <option value="pull_request">Pull request</option>
            </select>
          </div>
          <div className="field">
            <label>Its</label>
            <select value={form.match_field} onChange={(e) => update("match_field", e.target.value)}>
              <option value="title">Title</option>
              <option value="body">Description</option>
            </select>
          </div>
          <div className="field">
            <label>Contains</label>
            <input
              type="text"
              placeholder="e.g. bug"
              value={form.match_value}
              onChange={(e) => update("match_value", e.target.value)}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="field">
            <label><Tag size={12} style={{ verticalAlign: -1 }} /> Add label</label>
            <input
              type="text"
              placeholder="e.g. bug"
              value={form.action_add_label}
              onChange={(e) => update("action_add_label", e.target.value)}
            />
          </div>
          <div className="field" style={{ gridColumn: "span 2" }}>
            <label><MessageSquare size={12} style={{ verticalAlign: -1 }} /> Post comment</label>
            <input
              type="text"
              placeholder="e.g. Thanks for the report! Triaging now."
              value={form.action_comment_template}
              onChange={(e) => update("action_comment_template", e.target.value)}
            />
          </div>
        </div>

        <label className="checkbox-field">
          <input
            type="checkbox"
            checked={form.action_slack_notify}
            onChange={(e) => update("action_slack_notify", e.target.checked)}
          />
          <Slack size={13} /> Send a Slack notification
        </label>

        <div>
          <button className="btn btn-primary" type="submit" disabled={saving}>
            <Plus size={15} /> {saving ? "Adding…" : "Add rule"}
          </button>
        </div>
      </form>

      {rules === null && <div className="card">Loading rules…</div>}

      {rules && rules.length === 0 && (
        <div className="empty-state">
          <h3>No rules configured</h3>
          <p>Without a rule, the bot falls back to: issue title contains "bug" → label it and notify Slack.</p>
        </div>
      )}

      {rules && rules.length > 0 && rules.map((rule) => (
        <div className="card rule-card" key={rule.id}>
          <div>
            <div className="rule-summary">
              When a{rule.event_type === "issues" ? "n issue" : " pull request"}'s{" "}
              <strong>{rule.match_field}</strong> contains <span className="kw">"{rule.match_value}"</span>:
              {rule.action_add_label && <> add label <span className="kw">{rule.action_add_label}</span>,</>}
              {rule.action_comment_template && <> post a comment,</>}
              {rule.action_slack_notify && <> notify Slack</>}
            </div>
            <div className="rule-meta">Applies to {repoName(rule.repo_id)}</div>
          </div>
          <button className="btn btn-sm btn-danger-ghost" onClick={() => handleDelete(rule.id)}>
            <Trash2 size={13} />
          </button>
        </div>
      ))}
    </>
  );
}
