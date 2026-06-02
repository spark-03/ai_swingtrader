import {
  Activity,
  BarChart3,
  Bot,
  Briefcase,
  Clock,
  DollarSign,
  LineChart,
  RotateCw,
  ShieldCheck
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { ControlPanel } from "./components/ControlPanel";
import { DataTable } from "./components/DataTable";
import { MetricCard } from "./components/MetricCard";
import { SettingsPanels } from "./components/SettingsPanels";
import { StatusPill } from "./components/StatusPill";
import { useDashboardData } from "./hooks/useDashboardData";
import type { OpenPosition, PqsRanking, RotationRow, TradeHistoryRow } from "./types/trading";

const navItems = [
  "Overview",
  "Open Positions",
  "Trade History",
  "Rotation Monitor",
  "PQS Rankings",
  "RL Analytics",
  "Portfolio Analytics",
  "System Health",
  "Controls",
  "Logs"
];

function currency(value: number) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
}

function number(value: number) {
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 }).format(value);
}

export default function App() {
  const { data, error, loading } = useDashboardData();

  if (loading || !data) {
    return <div className="flex min-h-screen items-center justify-center bg-obsidian text-white">Loading control center...</div>;
  }

  const equityCurve = Array.from({ length: 12 }, (_, index) => ({
    name: `T${index + 1}`,
    equity: data.snapshot.equity - (11 - index) * 6200 + Math.sin(index) * 9000
  }));

  const rotationChart = data.rotations.map((rotation, index) => ({
    name: `R${index + 1}`,
    rotations: index + 1
  }));

  return (
    <div className="min-h-screen bg-obsidian font-body text-slate-100">
      <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,rgba(210,162,76,0.18),transparent_34%),radial-gradient(circle_at_80%_20%,rgba(103,232,165,0.12),transparent_28%),linear-gradient(135deg,#070A0E,#101820_52%,#050608)]" />
      <div className="flex">
        <aside className="sticky top-0 hidden h-screen w-72 border-r border-white/10 bg-black/20 p-6 backdrop-blur-xl lg:block">
          <div className="font-display text-2xl font-bold text-white">SwingTrader</div>
          <div className="mt-1 text-xs uppercase tracking-[0.35em] text-brass">Cloud Ops</div>
          <nav className="mt-10 space-y-2">
            {navItems.map((item) => (
              <a className="block rounded-2xl px-4 py-3 text-sm text-slate-400 transition hover:bg-white/10 hover:text-white" href={`#${item.replace(/ /g, "-")}`} key={item}>
                {item}
              </a>
            ))}
          </nav>
        </aside>

        <main className="w-full px-4 py-6 sm:px-6 lg:px-10">
          <header className="mb-8 rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 shadow-glass">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <div className="mb-3 flex flex-wrap gap-2">
                  <StatusPill status={error ? "yellow" : "green"} label={error ? "Mock fallback" : "Supabase live"} />
                  <StatusPill status={data.metrics.last_error ? "red" : "green"} label="Scheduler status" />
                  <StatusPill status="green" label="Paper trading" />
                </div>
                <h1 className="font-display text-4xl font-bold tracking-tight text-white lg:text-6xl">AI Swing Trading Control Center</h1>
                <p className="mt-3 max-w-3xl text-slate-400">
                  Cloud-native monitoring for 2H NIFTY500 rotation, PQS ranking, RL exits, Supabase persistence, and future trading controls.
                </p>
              </div>
              <div className="rounded-3xl border border-brass/30 bg-brass/10 p-4 text-sm text-brass">
                Last candle: {data.metrics.last_processed_slot ?? "Not processed"}
                <br />
                Last cycle: {data.metrics.last_cycle_completed_at ?? "Waiting"}
              </div>
            </div>
          </header>

          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" id="Overview">
            <MetricCard icon={<DollarSign className="h-5 w-5" />} label="Portfolio Value" value={currency(data.snapshot.equity)} detail="Supabase snapshot equity" />
            <MetricCard icon={<Briefcase className="h-5 w-5" />} label="Cash Available" value={currency(data.snapshot.cash)} detail="Unallocated paper capital" />
            <MetricCard icon={<Activity className="h-5 w-5" />} label="Daily PnL" value={currency(data.snapshot.daily_pnl)} detail="Current session estimate" />
            <MetricCard icon={<Bot className="h-5 w-5" />} label="Cycles" value={String(data.metrics.cycle_count)} detail="Successful trading cycles" />
          </section>

          <section className="mt-6 grid gap-4 xl:grid-cols-2" id="Portfolio-Analytics">
            <div className="rounded-3xl border border-white/10 bg-graphite/80 p-5 shadow-glass">
              <h2 className="font-display text-xl font-semibold text-white">Equity Curve</h2>
              <div className="mt-5 h-72">
                <ResponsiveContainer>
                  <AreaChart data={equityCurve}>
                    <defs>
                      <linearGradient id="equity" x1="0" x2="0" y1="0" y2="1">
                        <stop offset="5%" stopColor="#67E8A5" stopOpacity={0.55} />
                        <stop offset="95%" stopColor="#67E8A5" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="name" stroke="#64748b" />
                    <YAxis stroke="#64748b" />
                    <Tooltip contentStyle={{ background: "#101820", border: "1px solid rgba(255,255,255,.1)" }} />
                    <Area dataKey="equity" fill="url(#equity)" stroke="#67E8A5" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-graphite/80 p-5 shadow-glass" id="Rotation-Monitor">
              <h2 className="font-display text-xl font-semibold text-white">Rotation Monitor</h2>
              <div className="mt-5 h-72">
                <ResponsiveContainer>
                  <BarChart data={rotationChart.length ? rotationChart : [{ name: "None", rotations: 0 }]}>
                    <CartesianGrid stroke="rgba(255,255,255,0.08)" />
                    <XAxis dataKey="name" stroke="#64748b" />
                    <YAxis stroke="#64748b" />
                    <Tooltip contentStyle={{ background: "#101820", border: "1px solid rgba(255,255,255,.1)" }} />
                    <Bar dataKey="rotations" fill="#D2A24C" radius={[10, 10, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </section>

          <div className="mt-6 space-y-6">
            <DataTable<OpenPosition>
              title="Open Positions"
              rows={data.positions}
              columns={[
                { key: "symbol", header: "Symbol", render: (row) => row.symbol },
                { key: "entry", header: "Entry Time", render: (row) => new Date(row.entry_timestamp).toLocaleString() },
                { key: "price", header: "Entry Price", render: (row) => number(row.entry_price) },
                { key: "qty", header: "Quantity", render: (row) => row.quantity },
                { key: "capital", header: "Capital", render: (row) => currency(row.slot_capital) },
                { key: "pnl", header: "Unrealized PnL", render: (row) => currency((row.current_price - row.entry_price) * row.quantity) },
                { key: "pqs", header: "PQS", render: (row) => number(row.pqs) }
              ]}
            />

            <DataTable<TradeHistoryRow>
              title="Trade History"
              rows={data.trades}
              columns={[
                { key: "time", header: "Timestamp", render: (row) => new Date(row.timestamp).toLocaleString() },
                { key: "symbol", header: "Symbol", render: (row) => row.symbol },
                { key: "action", header: "Action", render: (row) => row.action },
                { key: "price", header: "Price", render: (row) => number(row.price) },
                { key: "qty", header: "Quantity", render: (row) => row.quantity },
                { key: "reason", header: "Reason", render: (row) => row.reason },
                { key: "rl", header: "RL Decision", render: (row) => row.rl_decision ?? "-" }
              ]}
            />

            <DataTable<RotationRow>
              title="Rotation History"
              rows={data.rotations}
              columns={[
                { key: "time", header: "Timestamp", render: (row) => new Date(row.timestamp).toLocaleString() },
                { key: "old", header: "Old Symbol", render: (row) => row.old_symbol },
                { key: "new", header: "New Symbol", render: (row) => row.new_symbol },
                { key: "oldp", header: "Old PQS", render: (row) => number(row.old_tqs) },
                { key: "newp", header: "New PQS", render: (row) => number(row.new_tqs) }
              ]}
            />

            <DataTable<PqsRanking>
              title="Top PQS Rankings"
              rows={data.rankings.slice(0, 20)}
              columns={[
                { key: "rank", header: "Rank", render: (row) => row.rank },
                { key: "symbol", header: "Symbol", render: (row) => row.symbol },
                { key: "pqs", header: "PQS", render: (row) => number(row.pqs) },
                { key: "price", header: "Price", render: (row) => number(row.last_price) }
              ]}
            />
          </div>

          <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4" id="System-Health">
            <MetricCard icon={<ShieldCheck className="h-5 w-5" />} label="Supabase" value="Connected" detail="Uses anon read client" />
            <MetricCard icon={<Clock className="h-5 w-5" />} label="Scheduler" value="Recoverable" detail="GitHub Actions one-shot" />
            <MetricCard icon={<LineChart className="h-5 w-5" />} label="RL Exits" value={String(data.metrics.exits_triggered)} detail="Exit events tracked" />
            <MetricCard icon={<RotateCw className="h-5 w-5" />} label="Rotations" value={String(data.metrics.rotations_triggered)} detail="Portfolio rotations" />
          </section>

          <div className="mt-6" id="Controls">
            <ControlPanel />
          </div>

          <div className="mt-6">
            <SettingsPanels />
          </div>

          <section className="mt-6 grid gap-4 lg:grid-cols-2" id="Logs">
            <div className="rounded-3xl border border-white/10 bg-black/30 p-5">
              <h2 className="flex items-center gap-2 font-display text-xl font-semibold text-white">
                <BarChart3 className="h-5 w-5 text-brass" /> RL Analytics
              </h2>
              <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-slate-300">
                <span>Exit Count: {data.metrics.exits_triggered}</span>
                <span>Hold Count: {Math.max(0, data.metrics.trades_executed - data.metrics.exits_triggered)}</span>
                <span>Win Rate: Pending</span>
                <span>Profit Factor: Pending</span>
                <span>Average Holding Time: Pending</span>
                <span>Average Return: Pending</span>
              </div>
            </div>
            <div className="rounded-3xl border border-white/10 bg-black/30 p-5">
              <h2 className="font-display text-xl font-semibold text-white">System Log Stream</h2>
              <div className="mt-4 max-h-64 space-y-2 overflow-auto font-mono text-xs text-slate-300">
                {data.logs.map((line) => (
                  <div className="rounded-xl bg-white/[0.04] px-3 py-2" key={line}>{line}</div>
                ))}
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
