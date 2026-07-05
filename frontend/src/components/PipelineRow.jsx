import { GitPullRequest, CircleDot, GitCommit, Tag, MessageSquare, Slack, ChevronRight, RotateCw } from "lucide-react";
import StatusBadge from "./StatusBadge";

const EVENT_ICON = {
  issues: CircleDot,
  pull_request: GitPullRequest,
  push: GitCommit,
};

const ACTION_ICON = {
  add_label: Tag,
  post_comment: MessageSquare,
  slack_notify: Slack,
};

const ACTION_LABEL = {
  add_label: "label",
  post_comment: "comment",
  slack_notify: "slack",
};

function eventTitle(event) {
  // We don't ship the raw payload to the frontend for size/privacy reasons;
  // repo + event + action already tells the story in this list.
  return `${event.event_type}${event.action ? `.${event.action}` : ""}`;
}

export default function PipelineRow({ event, onRetry }) {
  const Icon = EVENT_ICON[event.event_type] || CircleDot;
  const time = new Date(event.received_at);

  return (
    <div className="pipeline-row">
      <div className="pipeline-time">
        {time.toLocaleDateString(undefined, { month: "short", day: "numeric" })}
        <br />
        {time.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" })}
      </div>

      <div className="pipeline-flow">
        <div className="pipeline-node">
          <Icon size={15} />
          <span>{eventTitle(event)}</span>
        </div>
        <span className="pipeline-title">{event.repo_full_name}</span>

        {event.actions.length > 0 && (
          <>
            <ChevronRight size={14} className="pipeline-connector" />
            {event.actions.map((a) => {
              const AIcon = ACTION_ICON[a.action_type] || Tag;
              return (
                <span key={a.id} className={`action-chip ${a.status === "success" ? "success" : "failed"}`} title={a.detail || ""}>
                  <AIcon size={12} />
                  {ACTION_LABEL[a.action_type] || a.action_type}
                </span>
              );
            })}
          </>
        )}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <StatusBadge status={event.status} />
        {(event.status === "failed" || event.status === "processed_with_errors") && (
          <button className="btn btn-sm" onClick={() => onRetry(event.id)} title="Retry this event">
            <RotateCw size={13} />
          </button>
        )}
      </div>
    </div>
  );
}
