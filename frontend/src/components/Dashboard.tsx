
import { useEffect, useState } from "react";
import { getAdvice, getInsights, getStats } from "../api";
import type { Advice, Insights, PaceRow, StatRow, Stats } from "../types";
import { subtypeLabel as label } from "../labels";

const pct = (x: number) => `${Math.round(x * 100)}%`;

function Card({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-400">
        {title}
      </div>
      <div className="mt-1 text-2xl font-bold text-emerald-400">
        {value}
      </div>
    </div>
  );
}

function Bars({ title, rows }: { title: string; rows: StatRow[] }) {
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
        {title}
      </h2>

      {rows.length === 0 && (
        <p className="text-sm text-slate-500">No data yet.</p>
      )}

      {rows.map((r) => (
        <div key={r.key}>
          <div className="flex justify-between text-sm">
            <span>{label(r.key)}</span>
            <span className="font-mono text-slate-400">
              {pct(r.accuracy)} · {r.correct}/{r.attempted}
              {r.avg_time_seconds != null && ` · ${r.avg_time_seconds}s`}
            </span>
          </div>

          <div className="mt-1 h-2 rounded bg-slate-800">
            <div
              className={`h-2 rounded ${
                r.accuracy < 0.6 ? "bg-red-400" : "bg-emerald-400"
              }`}
              style={{
                width: `${Math.max(0, Math.min(100, r.accuracy * 100))}%`,
              }}
            />
          </div>
        </div>
      ))}
    </section>
  );
}

function PaceCell({
  title,
  hint,
  row,
}: {
  title: string;
  hint: string;
  row: PaceRow;
}) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-3">
      <div className="text-xs uppercase tracking-wide text-slate-400">
        {title}
      </div>

      <div className="text-xl font-bold text-emerald-400">
        {row.accuracy != null ? pct(row.accuracy) : "-"}
      </div>

      <div className="text-xs text-slate-500">
        {row.count} answers · {hint}
      </div>
    </div>
  );
}

export default function Dashboard({
  onBack,
}: {
  onBack: () => void;
}) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [advice, setAdvice] = useState<Advice | null>(null);
  const [adviceBusy, setAdviceBusy] = useState(false);
  const [adviceError, setAdviceError] = useState<string | null>(null);

  const [insights, setInsights] = useState<Insights | null>(null);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch((e: unknown) => {
        setError(
          e instanceof Error ? e.message : "Failed to load stats"
        );
      });

    getInsights()
      .then(setInsights)
      .catch(() => setInsights(null));
  }, []);

  async function loadAdvice() {
    setAdviceBusy(true);
    setAdviceError(null);

    try {
      setAdvice(await getAdvice());
    } catch (e) {
      setAdviceError(
        e instanceof Error ? e.message : "AI unavailable"
      );
    } finally {
      setAdviceBusy(false);
    }
  }

  if (error) {
    return <p className="text-red-300">{error}</p>;
  }

  if (!stats) {
    return <p className="text-slate-400">Loading...</p>;
  }

  const o = stats.overall;
  const maxDay = Math.max(1, ...stats.activity.map((d) => d.attempted));

  const budget = insights?.pace.budget_seconds ?? null;

  return (
    <div className="w-full max-w-2xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Your progress</h1>

        <button
          onClick={onBack}
          className="text-sm text-slate-400 underline hover:text-slate-200"
        >
          Back
        </button>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card title="Attempted" value={String(o.attempted)} />
        <Card title="Accuracy" value={pct(o.accuracy)} />
        <Card title="Marks" value={o.marks.toFixed(2)} />
        <Card
          title="Avg time"
          value={
            o.avg_time_seconds != null
              ? `${o.avg_time_seconds}s`
              : "-"
          }
        />
      </div>

      {stats.weak_topics.length > 0 && (
        <div className="rounded-lg border border-red-400/40 bg-red-400/5 p-4">
          <h2 className="font-semibold text-red-300">
            Focus on these
          </h2>

          <ul className="mt-1 text-sm text-slate-300">
            {stats.weak_topics.map((w) => (
              <li key={w.key}>
                {label(w.key)}: {pct(w.accuracy)} over {w.attempted} questions
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* AI-powered study advice */}
      <section className="space-y-2">
        {advice && (
          <div className="space-y-2 rounded-lg border border-sky-400/40 bg-sky-400/5 p-4">
            <h2 className="font-semibold text-sky-200">
              Study advice (AI)
            </h2>

            <p className="text-sm text-slate-200">
              {advice.summary}
            </p>

            <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
              {advice.actions.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
        )}

        {adviceError && (
          <p className="text-sm text-amber-300" role="alert">
            {adviceError}
          </p>
        )}

        <button
          onClick={loadAdvice}
          disabled={adviceBusy}
          className="text-sm text-sky-300 underline hover:text-sky-200 disabled:opacity-50"
        >
          {adviceBusy
            ? "Asking Gemini..."
            : advice
              ? "Refresh advice"
              : "Get study advice (AI)"}
        </button>
      </section>

      {/* Repeated mistake patterns and trap analysis */}
      {insights && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Your repeated mistakes
          </h2>

          {insights.patterns.length === 0 && (
            <p className="text-sm text-slate-500">
              No tagged mistakes yet. They are recorded as you practise.
            </p>
          )}

          {insights.patterns.map((p) => (
            <div
              key={p.tag}
              className="rounded-lg border border-slate-800 bg-slate-900 p-3"
            >
              <div className="flex justify-between text-sm">
                <span>{label(p.subtype)}</span>
                <span className="font-mono text-red-300">
                  {p.count}×
                </span>
              </div>

              {p.note && (
                <p className="mt-1 text-sm text-slate-300">
                  {p.note}
                </p>
              )}

              {p.example && (
                <p className="mt-1 text-xs text-slate-500">
                  Example: {p.example}
                </p>
              )}
            </div>
          ))}

          {insights.untagged_wrong > 0 && (
            <p className="text-xs text-slate-500">
              {insights.untagged_wrong} wrong answers matched no standard
              mistake (or were answered before tags existed).
            </p>
          )}
        </section>
      )}

      {/* Pace and accuracy analysis */}
      {insights && insights.pace.timed_answers > 0 && (
        <section className="space-y-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
            Pace and accuracy
          </h2>

          <div className="grid grid-cols-3 gap-3">
            <PaceCell
              title="Rushed"
              row={insights.pace.rushed}
              hint={budget ? `under ${Math.floor(budget / 4)}s` : "very fast"}
            />

            <PaceCell
              title="Steady"
              row={insights.pace.steady}
              hint={budget ? `up to ${budget}s` : "within the time"}
            />

            <PaceCell
              title="Slow"
              row={insights.pace.slow}
              hint={budget ? `over ${budget}s` : "over the time"}
            />
          </div>

          {insights.pace.flags.map((f, i) => (
            <p
              key={i}
              className="rounded-lg bg-amber-400/10 p-3 text-sm text-amber-200"
            >
              {f}
            </p>
          ))}
        </section>
      )}

      <Bars title="By question type" rows={stats.by_subtype} />

      <Bars title="By difficulty" rows={stats.by_difficulty} />

      <section className="space-y-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Last 14 days
        </h2>

        <div className="flex h-24 items-end gap-1">
          {stats.activity.map((d) => (
            <div
              key={d.date}
              title={`${d.date}: ${d.correct}/${d.attempted}`}
              className="flex-1 rounded-t bg-emerald-400/70"
              style={{
                height: `${(d.attempted / maxDay) * 100}%`,
                minHeight: d.attempted ? 4 : 1,
              }}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
