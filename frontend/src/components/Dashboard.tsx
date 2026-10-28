import { useEffect, useState } from "react";
import { getStats } from "../api";
import type { StatRow, Stats } from "../types";

const pct = (x: number) => `${Math.round(x * 100)}%`;
const label = (k: string) => k.replace(/_/g, " ");

function Card({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-400">{title}</div>
      <div className="mt-1 text-2xl font-bold text-emerald-400">{value}</div>
    </div>
  );
}

function Bars({ title, rows }: { title: string; rows: StatRow[] }) {
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">{title}</h2>
      {rows.length === 0 && <p className="text-sm text-slate-500">No data yet.</p>}
      {rows.map((r) => (
        <div key={r.key}>
          <div className="flex justify-between text-sm">
            <span className="capitalize">{label(r.key)}</span>
            <span className="font-mono text-slate-400">
              {pct(r.accuracy)} · {r.correct}/{r.attempted}
              {r.avg_time_seconds != null && ` · ${r.avg_time_seconds}s`}
            </span>
          </div>
          <div className="mt-1 h-2 rounded bg-slate-800">
            <div
              className={`h-2 rounded ${r.accuracy < 0.6 ? "bg-red-400" : "bg-emerald-400"}`}
              style={{ width: `${r.accuracy * 100}%` }}
            />
          </div>
        </div>
      ))}
    </section>
  );
}

export default function Dashboard({ onBack }: { onBack: () => void }) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="text-red-300">{error}</p>;
  if (!stats) return <p className="text-slate-400">Loading...</p>;

  const o = stats.overall;
  const maxDay = Math.max(1, ...stats.activity.map((d) => d.attempted));

  return (
    <div className="w-full max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Your progress</h1>
        <button onClick={onBack} className="text-sm text-slate-400 underline hover:text-slate-200">
          Back
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card title="Attempted" value={String(o.attempted)} />
        <Card title="Accuracy" value={pct(o.accuracy)} />
        <Card title="Marks" value={o.marks.toFixed(2)} />
        <Card title="Avg time" value={o.avg_time_seconds != null ? `${o.avg_time_seconds}s` : "-"} />
      </div>

      {stats.weak_topics.length > 0 && (
        <div className="rounded-lg border border-red-400/40 bg-red-400/5 p-4">
          <h2 className="font-semibold text-red-300">Focus on these</h2>
          <ul className="mt-1 text-sm text-slate-300">
            {stats.weak_topics.map((w) => (
              <li key={w.key} className="capitalize">
                {label(w.key)}: {pct(w.accuracy)} over {w.attempted} questions
              </li>
            ))}
          </ul>
        </div>
      )}

      <Bars title="By question type" rows={stats.by_subtype} />
      <Bars title="By difficulty" rows={stats.by_difficulty} />

      <section className="space-y-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Last 14 days</h2>
        <div className="flex h-24 items-end gap-1">
          {stats.activity.map((d) => (
            <div
              key={d.date}
              title={`${d.date}: ${d.correct}/${d.attempted}`}
              className="flex-1 rounded-t bg-emerald-400/70"
              style={{ height: `${(d.attempted / maxDay) * 100}%`, minHeight: d.attempted ? 4 : 1 }}
            />
          ))}
        </div>
      </section>
    </div>
  );
}