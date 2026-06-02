import { AlertTriangle, Pause, Play, RotateCcw, ShieldAlert } from "lucide-react";
import type { TradingMode } from "../types/trading";

const disabledButton =
  "rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-300 transition hover:border-brass/60 hover:text-white disabled:cursor-not-allowed disabled:opacity-50";

export function ControlPanel() {
  const modes: TradingMode[] = ["Research", "Backtest", "Paper Trading", "Live Trading"];

  return (
    <section className="grid gap-4 lg:grid-cols-3">
      <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
        <h2 className="font-display text-xl font-semibold text-white">Bot Control</h2>
        <p className="mt-2 text-sm text-slate-400">Backend actions are disabled until explicit live-control APIs exist.</p>
        <div className="mt-5 grid grid-cols-2 gap-3">
          <button className={disabledButton} disabled><Play className="mb-2 h-4 w-4" />Start Bot</button>
          <button className={disabledButton} disabled><Pause className="mb-2 h-4 w-4" />Stop Bot</button>
          <button className={disabledButton} disabled><RotateCcw className="mb-2 h-4 w-4" />Force Cycle</button>
          <button className={disabledButton} disabled><ShieldAlert className="mb-2 h-4 w-4" />Safe Mode</button>
        </div>
      </div>

      <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
        <h2 className="font-display text-xl font-semibold text-white">Trading Mode</h2>
        <div className="mt-5 grid gap-3">
          {modes.map((mode) => (
            <button className={disabledButton} disabled={mode === "Live Trading"} key={mode}>
              {mode}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-3xl border border-danger/30 bg-danger/10 p-5">
        <h2 className="flex items-center gap-2 font-display text-xl font-semibold text-white">
          <AlertTriangle className="h-5 w-5 text-danger" /> Emergency Controls
        </h2>
        <p className="mt-2 text-sm text-slate-300">Confirmation-gated controls for future live trading operations.</p>
        <div className="mt-5 grid gap-3">
          {["Close All Positions", "Disable Entries", "Disable Rotations", "Enable Safe Mode"].map((label) => (
            <button className={disabledButton} disabled key={label}>{label}</button>
          ))}
        </div>
      </div>
    </section>
  );
}
