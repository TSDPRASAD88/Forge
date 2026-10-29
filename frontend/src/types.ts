
export type Exam = "gate_cse" | "ssc_cgl";
export type Difficulty = "easy" | "medium" | "hard";
export type Topic = "percentages" | "ratios" | "profit_loss" | "time_work" | "averages_mixtures" | "interest";;

export interface Profile {
  exam: Exam;
  name: string;
  description: string;
  seconds_per_question: number;
  marks_correct: number;
  marks_negative: number;
}

export interface PublicQuestion {
  id: string;
  topic: string;
  subtype: string;
  difficulty: Difficulty;
  text: string;
  unit: string;
  options: string[];
}

export interface Session {
  id: string;
  exam: Exam;
  created_at: string;
  questions: PublicQuestion[];
  answered: string[];
}

export interface SolutionStep {
  description: string;
  expression: string | null;
  result: string | null;
}

export interface AnswerResult {
  correct: boolean;
  skipped: boolean;
  marks: number;
  correct_index: number;
  correct_answer: string;
  steps: SolutionStep[];
  explanation: string | null;
}

export interface StatRow {
  key: string;
  attempted: number;
  correct: number;
  skipped: number;
  accuracy: number;
  marks: number;
  avg_time_seconds: number | null;
}

export interface Stats {
  overall: StatRow;
  by_subtype: StatRow[];
  by_difficulty: StatRow[];
  weak_topics: StatRow[];
  activity: { date: string; attempted: number; correct: number }[];
}

export interface Advice {
  summary: string;
  actions: string[];
  cached: boolean;
}
