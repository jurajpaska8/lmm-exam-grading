"""Grading-agreement statistics from data/scores_per_question.csv.

Prints total-points agreement (mean difference, MSE, higher/lower/equal) and
per-question Pearson correlations between the human grader (M), Qwen3.6 (Q)
and Gemma4 (G). All scores are normalized to [0, 1] per question, so a total
score is at most 8 points.
"""
from helpers.statistics_helper import calculate_correlation
import csv

CSV_PATH = "data/scores_per_question.csv"
NUM_QUESTIONS = 8
GRADERS = {"M": "human", "Q": "qwen3.6", "G": "gemma4:31b"}


def read_scores(csv_path: str) -> list[dict[str, float | None]]:
    with open(csv_path, encoding="utf-8", newline="") as f:
        rows = []
        for row in csv.DictReader(f):
            scores = {}
            for grader in GRADERS:
                for i in range(1, NUM_QUESTIONS + 1):
                    value = row[f"{grader}{i}"].strip()
                    # Empty cell = no valid entry in the model response
                    scores[f"{grader}{i}"] = float(value) if value else None
            rows.append(scores)
    return rows


def total(row: dict[str, float | None], grader: str) -> float:
    # A question without a valid entry counts as 0 points in the total
    return sum(row[f"{grader}{i}"] or 0.0 for i in range(1, NUM_QUESTIONS + 1))


def delta_stats(deltas: list[float]) -> dict[str, float]:
    count = len(deltas)
    return {
        "avg": sum(deltas) / count,
        "mse": sum(d * d for d in deltas) / count,
        "higher": sum(1 for d in deltas if d > 1e-9),
        "lower": sum(1 for d in deltas if d < -1e-9),
        "equal": sum(1 for d in deltas if abs(d) <= 1e-9),
    }


rows = read_scores(CSV_PATH)
print(f"Submissions: {len(rows)}")

print("\nTotal-points agreement (out of 8); delta = first minus second:")
for first, second in (("Q", "M"), ("G", "M"), ("G", "Q")):
    deltas = [total(r, first) - total(r, second) for r in rows]
    s = delta_stats(deltas)
    print(f"  {first} vs {second}: avg delta={s['avg']:.2f}, MSE={s['mse']:.2f}, "
          f"higher={s['higher']}, lower={s['lower']}, equal={s['equal']}")

print("\nPer-question Pearson correlation (missing entries left out):")
for first, second in (("M", "Q"), ("M", "G"), ("Q", "G")):
    values = []
    for i in range(1, NUM_QUESTIONS + 1):
        pairs = [(r[f"{first}{i}"], r[f"{second}{i}"]) for r in rows
                 if r[f"{first}{i}"] is not None and r[f"{second}{i}"] is not None]
        x, y = zip(*pairs)
        values.append(f"{calculate_correlation(list(x), list(y)):.2f}")
    print(f"  {first} vs {second}: " + "  ".join(f"Q{i}={v}" for i, v in enumerate(values, start=1)))
