const STATUS_MAP = {
  processed: { label: "Processed", cls: "badge-success" },
  processed_with_errors: { label: "Partial", cls: "badge-pending" },
  failed: { label: "Failed", cls: "badge-fail" },
  received: { label: "Queued", cls: "badge-info" },
  processing: { label: "Processing", cls: "badge-pending" },
  duplicate: { label: "Duplicate", cls: "badge-info" },
};

export default function StatusBadge({ status }) {
  const meta = STATUS_MAP[status] || { label: status, cls: "badge-info" };
  return <span className={`badge ${meta.cls}`}>{meta.label}</span>;
}
