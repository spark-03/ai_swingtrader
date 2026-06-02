const inputClass = "w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none";

function SettingsCard({ title, fields }: { title: string; fields: string[] }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-5">
      <h2 className="font-display text-xl font-semibold text-white">{title}</h2>
      <div className="mt-5 grid gap-3">
        {fields.map((field) => (
          <label className="text-sm text-slate-400" key={field}>
            {field}
            <input className={`${inputClass} mt-2`} disabled placeholder="Read-only preview" />
          </label>
        ))}
      </div>
    </div>
  );
}

export function SettingsPanels() {
  return (
    <section className="grid gap-4 lg:grid-cols-3">
      <SettingsCard title="Risk Management" fields={["Max Drawdown", "Max Position Size", "Max Exposure", "Max Open Positions"]} />
      <SettingsCard title="PQS Settings" fields={["Minimum PQS", "Top Candidates Count", "Rotation Threshold", "Rebalance Frequency"]} />
      <SettingsCard title="RL Settings" fields={["Confidence Threshold", "Hold Time", "Exit Aggressiveness"]} />
    </section>
  );
}
