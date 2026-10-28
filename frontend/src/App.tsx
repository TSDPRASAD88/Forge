import { useState } from "react";
import Practice from "./components/Practice";
import Setup from "./components/Setup";
import type { AnswerResult, Session } from "./types";

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [results, setResults] = useState<AnswerResult[] | null>(null);

  let view;
  if (results && session) {
    const correct = results.filter((r) => r.correct).length;
    const skipped = results.filter((r) => r.skipped).length;
    const marks = results.reduce((sum, r) => sum + r.marks, 0);
    view = (
      <div className="w-full max-w-xl space-y-4 text-center">
        <h1 className="text-3xl font-bold">Session complete</h1>
        <p className="text-5xl font-bold text-emerald-400">
          {correct}/{session.questions.length}
        </p>
        <p className="text-slate-400">
          {marks.toFixed(2)} marks · {skipped} skipped · {results.length - correct - skipped} wrong
        </p>
        <button
          onClick={() => {
            setSession(null);
            setResults(null);
          }}
          className="rounded-lg bg-emerald-500 px-6 py-3 font-semibold text-slate-950 hover:bg-emerald-400"
        >
          Practice again
        </button>
      </div>
    );
  } else if (session) {
    view = <Practice key={session.id} session={session} onFinish={setResults} />;
  } else {
    view = <Setup onStart={setSession} />;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 p-6 text-slate-100">
      {view}
    </div>
  );
}