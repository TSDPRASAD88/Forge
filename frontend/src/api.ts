import type { AnswerResult, Difficulty, Exam, Profile, Session } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ? JSON.stringify(body.detail) : `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const getProfiles = () => request<Profile[]>("/profiles");

export const createSession = (body: {
  exam: Exam;
  difficulty: Difficulty | null;
  count: number;
}) => request<Session>("/sessions", { method: "POST", body: JSON.stringify(body) });

export const submitAnswer = (
  sessionId: string,
  body: { question_id: string; selected_index: number | null; time_taken_seconds: number },
) =>
  request<AnswerResult>(`/sessions/${sessionId}/answers`, {
    method: "POST",
    body: JSON.stringify(body),
  });