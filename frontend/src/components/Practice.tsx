
import { useRef, useState } from "react";
import { submitAnswer } from "../api";
import type { AnswerResult, Session } from "../types";

interface Props {
  session: Session;
  onFinish: (results: AnswerResult[]) => void;
}

export default function Practice({ session, onFinish }: Props) {
  const [index, setIndex] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [results, setResults] = useState<AnswerResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const startedAt = useRef(Date.now());

  const q = session.questions[index];
  const isLast = index === session.questions.length - 1;

  async function answer(choice: number | null) {
    if (result || busy) return;

    setBusy(true);
    setError(null);
    setSelected(choice);

    try {
      const r = await submitAnswer(session.id, {
        question_id: q.id,
        selected_index: choice,
        time_taken_seconds: (Date.now() - startedAt.current) / 1000,
      });

      setResult(r);
      setResults((prev) => [...prev, r]);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : "Could not submit answer"
      );
      setSelected(null);
    } finally {
      setBusy(false);
    }
  }

  function next() {
    if (isLast) {
      onFinish(results);
      return;
    }

    setIndex((i) => i + 1);
    setSelected(null);
    setResult(null);
    setError(null);
    startedAt.current = Date.now();
  }

  function optionClass(i: number) {
    const base =
      "flex w-full items-center gap-3 rounded-lg border px-4 py-3 text-left transition";

    if (!result) {
      return `${base} border-slate-700 hover:border-emerald-400 hover:bg-slate-900`;
    }

    if (i === result.correct_index) {
      return `${base} border-emerald-400 bg-emerald-400/10`;
    }

    if (i === selected) {
      return `${base} border-red-400 bg-red-400/10`;
    }

    return `${base} border-slate-800 opacity-50`;
  }

  return (
    <div className="w-full max-w-xl space-y-5">
      <div className="flex items-center justify-between text-sm text-slate-400">
        <span>
          Question {index + 1} of {session.questions.length}
        </span>

        <span className="rounded bg-slate-800 px-2 py-0.5 text-xs uppercase">
          {q.difficulty}
        </span>
      </div>

      <div className="h-1.5 rounded bg-slate-800">
        <div
          className="h-1.5 rounded bg-emerald-400 transition-all"
          style={{
            width: `${((index + 1) / session.questions.length) * 100}%`,
          }}
        />
      </div>

      <h2 className="text-2xl font-semibold leading-snug">{q.text}</h2>

      {q.unit && (
        <p className="text-sm text-slate-400">Answer in {q.unit}</p>
      )}

      <div className="space-y-2">
        {q.options.map((opt, i) => (
          <button
            key={i}
            onClick={() => answer(i)}
            disabled={!!result || busy}
            className={optionClass(i)}
          >
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-800 text-sm font-semibold">
              {"ABCD"[i]}
            </span>

            <span className="font-mono">{opt}</span>
          </button>
        ))}
      </div>

      {error && (
        <p className="rounded-lg bg-red-500/10 p-3 text-sm text-red-300">
          {error}
        </p>
      )}

      {!result && (
        <button
          onClick={() => answer(null)}
          disabled={busy}
          className="text-sm text-slate-400 underline hover:text-slate-200"
        >
          Skip this question
        </button>
      )}

      {result && (
        <div className="space-y-3 rounded-lg border border-slate-800 bg-slate-900 p-4">
          <p
            className={`font-semibold ${
              result.correct
                ? "text-emerald-400"
                : result.skipped
                  ? "text-slate-300"
                  : "text-red-400"
            }`}
          >
            {result.skipped
              ? "Skipped"
              : result.correct
                ? "Correct!"
                : "Incorrect"}{" "}
            <span className="font-mono text-sm">
              ({result.marks > 0 ? "+" : ""}
              {result.marks} marks)
            </span>
          </p>

          <p className="text-sm text-slate-300">
            Answer:{" "}
            <span className="font-mono text-emerald-300">
              {result.correct_answer}
            </span>
          </p>

          {result.explanation && (
            <p className="rounded bg-red-400/10 p-3 text-sm text-red-200">
              <span className="font-semibold">Why that was wrong: </span>
              {result.explanation}
            </p>
          )}

          <ol className="list-decimal space-y-2 pl-5 text-sm text-slate-300">
            {result.steps.map((s, i) => (
              <li key={i}>
                {s.description}

                {s.expression && (
                  <div className="font-mono text-slate-100">
                    {s.expression}
                  </div>
                )}

                {s.result && (
                  <div className="font-mono text-emerald-300">
                    = {s.result}
                  </div>
                )}
              </li>
            ))}
          </ol>

          <button
            onClick={next}
            className="w-full rounded-lg bg-emerald-500 py-2.5 font-semibold text-slate-950 hover:bg-emerald-400"
          >
            {isLast ? "Finish" : "Next question"}
          </button>
        </div>
      )}
    </div>
  );
}
