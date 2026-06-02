import type { HealthStatus } from "../types/trading";

const styles: Record<HealthStatus, string> = {
  green: "bg-mint/15 text-mint ring-mint/30",
  yellow: "bg-brass/15 text-brass ring-brass/30",
  red: "bg-danger/15 text-danger ring-danger/30"
};

export function StatusPill({ status, label }: { status: HealthStatus; label: string }) {
  return <span className={`rounded-full px-3 py-1 text-xs ring-1 ${styles[status]}`}>{label}</span>;
}
