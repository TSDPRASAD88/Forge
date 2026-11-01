"""Writes review_sheet.md: sample questions for every question type, so you can read them as a learner would.

Run from backend/:  python -m app.tools.review_sheet
Then open review_sheet.md in VS Code and press Cmd+Shift+V for the preview.
"""

from pathlib import Path

from app.domain.enums import Difficulty, ExamType
from app.engine.generator import all_subtypes, generate_question


def main(per_subtype: int = 3) -> None:
    lines = [
        "# Review sheet",
        "",
        "Look for: unclear wording, unrealistic numbers, steps that skip a idea, and wrong-option notes that do not fit.",
        "",
    ]
    difficulties = list(Difficulty)
    for subtype, topic in sorted(all_subtypes().items(), key=lambda kv: (kv[1].value, kv[0])):
        lines += [f"## {topic.value} / {subtype}", ""]
        for i in range(per_subtype):
            d = difficulties[i % len(difficulties)]
            q = generate_question(ExamType.SSC_CGL, d, topic=topic, subtype=subtype, seed=1000 + i)
            lines += [f"**{d.value}** (seed {q.seed}): {q.text}", ""]
            for j, opt in enumerate(q.options):
                if j == q.correct_index:
                    lines.append(f"- {'ABCD'[j]}) {opt}  ✓")
                else:
                    lines.append(f"- {'ABCD'[j]}) {opt}  _{q.distractor_tags[opt]}_ {q.distractor_notes[opt]}")
            lines.append("")
            for n, s in enumerate(q.steps, 1):
                result = f" = {s.result}" if s.result else ""
                lines.append(f"  {n}. {s.description} `{s.expression or ''}`{result}")
            lines.append("")
    out = Path("review_sheet.md")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out.resolve()}  ({len(all_subtypes())} question types x {per_subtype} samples)")


if __name__ == "__main__":
    main()