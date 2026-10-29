
import type {
  AnswerResult,
  Difficulty,
  Exam,
  Profile,
  Session,
  Stats,
  Advice,
  Topic,
} from "./types";

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);

    throw new Error(
      typeof body?.detail === "string"
        ? body.detail
        : body?.detail
          ? JSON.stringify(body.detail)
          : `Request failed (${res.status})`,
    );
  }

  return res.json() as Promise<T>;
}

export const getProfiles = () => request<Profile[]>("/profiles");

export const getStats = () => request<Stats>("/stats");

export const getAdvice = () =>
  request<Advice>("/stats/advice", { method: "POST" });

export const createSession = (body: {
  exam: Exam;
  topic: Topic | null;
  difficulty: Difficulty | null;
  count: number;
}) =>
  request<Session>("/sessions", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const submitAnswer = (
  sessionId: string,
  body: {
    question_id: string;
    selected_index: number | null;
    time_taken_seconds: number;
  },
) =>
  request<AnswerResult>(`/sessions/${sessionId}/answers`, {
    method: "POST",
    body: JSON.stringify(body),
  });

export const explainQuestion = (
  sessionId: string,
  questionId: string,
) =>
  request<{ explanation: string; cached: boolean }>(
    `/sessions/${sessionId}/questions/${questionId}/explain`,
    { method: "POST" },
  );
