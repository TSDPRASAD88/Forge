"""Quality report: how many wrong options are real mistakes (not filler), and how varied the questions are.

Run from backend/:  python -m app.tools.quality_report          (worst 25 rows)
                    python -m app.tools.quality_report --all    (every row)
"""

import sys

from app.domain.enums import Difficulty, ExamType
from app.engine.generator import all_subtypes, generate_question
from app.services.practice import fingerprint

SAMPLES = 300


def main(show_all: bool = False, samples: int = SAMPLES) -> None:
    rows = []
    for subtype, topic in all_subtypes().items():
        for difficulty in Difficulty:
            real_counts: list[int] = []
            texts: set[str] = set()
            for seed in range(samples):
                q = generate_question(ExamType.SSC_CGL, difficulty, topic=topic, subtype=subtype, seed=seed)
                real_counts.append(sum(1 for t in q.distractor_tags.values() if not t.endswith(":filler")))
                texts.add(fingerprint(q.subtype, q.params))
            n = len(real_counts)
            rows.append(
                (
                    sum(real_counts) / n,
                    subtype,
                    difficulty.value,
                    100 * sum(1 for r in real_counts if r == 0) / n,
                    100 * len(texts) / n,
                )
            )

    rows.sort()
    overall = sum(r[0] for r in rows) / len(rows)
    print(f"{'subtype':<22}{'difficulty':<11}{'real traps (of 3)':>18}{'no real trap %':>16}{'unique qs %':>16}")
    for avg, subtype, diff, zero, uniq in rows if show_all else rows[:25]:
        print(f"{subtype:<22}{diff:<11}{avg:>18.2f}{zero:>16.1f}{uniq:>16.1f}")
    print(f"\nOverall average real traps per question: {overall:.2f} of 3  ({len(rows)} subtype/difficulty rows)")


if __name__ == "__main__":
    main(show_all="--all" in sys.argv)