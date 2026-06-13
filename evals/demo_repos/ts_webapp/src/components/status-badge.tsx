type Props = {
  status: "ready" | "indexing" | "failed";
};


export function StatusBadge({ status }: Props) {
  const label = status === "ready" ? "Ready" : status === "indexing" ? "Indexing" : "Failed";
  return <span data-status={status}>{label}</span>;
}
