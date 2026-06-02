import type { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  value: string;
  detail?: string;
  icon?: ReactNode;
}

export function MetricCard({ label, value, detail, icon }: MetricCardProps) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 shadow-glass backdrop-blur">
      <div className="flex items-center justify-between text-slate-400">
        <span className="text-xs uppercase tracking-[0.3em]">{label}</span>
        {icon}
      </div>
      <div className="mt-4 font-display text-3xl font-semibold text-white">{value}</div>
      {detail ? <div className="mt-2 text-sm text-slate-400">{detail}</div> : null}
    </div>
  );
}
