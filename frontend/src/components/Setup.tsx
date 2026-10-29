
import { useEffect, useState } from "react";
import { createSession, getProfiles } from "../api";
import type { Difficulty, Exam, Profile, Session, Topic } from "../types";

interface Props {
  onStart: (session: Session) => void;
}

const DIFFICULTIES: { value: Difficulty | null; label: string }[] = [
  { value: null, label: "Mixed" },
  { value: "easy", label: "Easy" },
  { value: "medium", label: "Medium" },
  { value: "hard", label: "Hard" },
];

const TOPICS: { value: Topic | null; label: string }[] = [
  { value: null, label: "Mixed" },
  { value: "percentages", label: "Percentages" },
  { value: "ratios", label: "Ratios & proportion" },
  { value: "profit_loss", label: "Profit & loss" },
];

export default function Setup({ onStart }: Props) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [exam, setExam] = useState<Exam>("ssc_cgl");
  const [topic, setTopic] = useState<Topic | null>(null);
  const [difficulty, setDifficulty] = useState<Difficulty | null>(null);
  const [count, setCount] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProfiles()
      .then(setProfiles)
      .catch((e) => setError(String(e.message ?? e)));
  }, []);

  async function start() {
    setLoading(true);
    setError(null);

    try {
      onStart(await createSession({ exam, topic, difficulty, count }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
      setLoading(false);
    }
  }

  const chip = (active: boolean) =>
    `rounded-lg border px-4 py-2 text-sm transition ${
      active
        ? "border-emerald-400 bg-emerald-400/10 text-emerald-300"
        : "border-slate-700 text-slate-300 hover:border-slate-500"
    }`;

  return (
    <div className="w-full max-w-xl space-y-6">
      <div>
        <h1 className="text-4xl font-bold">Aptitude Forge</h1>
        <p className="mt-1 text-slate-400">
          Aptitude practice with verified answers.
        </p>
      </div>

      <section className="space-y-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Exam
        </h2>

        <div className="grid gap-2">
          {profiles.map((p) => (
            <button
              key={p.exam}
              onClick={() => setExam(p.exam)}
              className={`text-left ${chip(exam === p.exam)}`}
            >
              <div className="font-medium">{p.name}</div>
              <div className="text-xs opacity-70">
                +{p.marks_correct} / -{p.marks_negative.toFixed(2)} marks ·{" "}
                {p.seconds_per_question}s per question
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Topic
        </h2>

        <div className="flex flex-wrap gap-2">
          {TOPICS.map((t) => (
            <button
              key={t.label}
              onClick={() => setTopic(t.value)}
              className={chip(topic === t.value)}
            >
              {t.label}
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Difficulty
        </h2>

        <div className="flex flex-wrap gap-2">
          {DIFFICULTIES.map((d) => (
            <button
              key={d.label}
              onClick={() => setDifficulty(d.value)}
              className={chip(difficulty === d.value)}
            >
              {d.label}
            </button>
          ))}
        </div>
      </section>

      <section className="space-y-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
          Questions
        </h2>

        <div className="flex gap-2">
          {[5, 10, 20].map((n) => (
            <button
              key={n}
              onClick={() => setCount(n)}
              className={chip(count === n)}
            >
              {n}
            </button>
          ))}
        </div>
      </section>

      {error && (
        <p className="rounded-lg bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      <button
        onClick={start}
        disabled={loading || profiles.length === 0}
        className="w-full rounded-lg bg-emerald-500 py-3 font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:opacity-50"
      >
        {loading ? "Generating & verifying questions..." : "Start practice"}
      </button>
    </div>
  );
}
