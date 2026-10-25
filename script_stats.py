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

print("\nTotal-score Pearson correlation, mean difference and mean |difference| as % of the maximum (8):")
for first, second in (("Q", "M"), ("G", "M"), ("G", "Q")):
    totals_first = [total(r, first) for r in rows]
    totals_second = [total(r, second) for r in rows]
    deltas = [a - b for a, b in zip(totals_first, totals_second)]
    print(f"  {first} vs {second}: r={calculate_correlation(totals_second, totals_first):.2f}, "
          f"mean diff={100 * sum(deltas) / len(deltas) / NUM_QUESTIONS:.1f}%, "
          f"mean |diff|={100 * sum(abs(d) for d in deltas) / len(deltas) / NUM_QUESTIONS:.1f}%")

print("\nPer-question Pearson correlation (missing entries left out):")
for first, second in (("M", "Q"), ("M", "G"), ("Q", "G")):
    values = []
    for i in range(1, NUM_QUESTIONS + 1):
        pairs = [(r[f"{first}{i}"], r[f"{second}{i}"]) for r in rows
                 if r[f"{first}{i}"] is not None and r[f"{second}{i}"] is not None]
        x, y = zip(*pairs)
        values.append(f"{calculate_correlation(list(x), list(y)):.2f}")
    print(f"  {first} vs {second}: " + "  ".join(f"Q{i}={v}" for i, v in enumerate(values, start=1)))


# --- Spread, uncertainty and model comparison -------------------------------
# Dependency-free resampling with a fixed seed, so the numbers are reproducible.
import random
import statistics

N_RESAMPLES = 10000
SEED = 2026


def bootstrap_ci(values: list[float], stat=statistics.mean, level: float = 0.95) -> tuple[float, float]:
    rng = random.Random(SEED)
    estimates = sorted(stat(rng.choices(values, k=len(values))) for _ in range(N_RESAMPLES))
    low = estimates[int((1 - level) / 2 * N_RESAMPLES)]
    high = estimates[int((1 + level) / 2 * N_RESAMPLES) - 1]
    return low, high


def sign_flip_p(values: list[float]) -> float:
    """Two-sided paired permutation test of mean(values) == 0."""
    rng = random.Random(SEED)
    observed = abs(statistics.mean(values))
    hits = sum(abs(statistics.mean([v if rng.random() < 0.5 else -v for v in values])) >= observed - 1e-12
               for _ in range(N_RESAMPLES))
    return (hits + 1) / (N_RESAMPLES + 1)


def group_permutation_p(group_a: list[float], group_b: list[float]) -> float:
    """Two-sided permutation test of mean(group_a) == mean(group_b)."""
    rng = random.Random(SEED)
    pooled = group_a + group_b
    observed = abs(statistics.mean(group_a) - statistics.mean(group_b))
    hits = 0
    for _ in range(N_RESAMPLES):
        rng.shuffle(pooled)
        a, b = pooled[:len(group_a)], pooled[len(group_a):]
        hits += abs(statistics.mean(a) - statistics.mean(b)) >= observed - 1e-12
    return (hits + 1) / (N_RESAMPLES + 1)


print(f"\nSpread of total-score differences (bootstrap 95% CI, {N_RESAMPLES} resamples):")
for first, second in (("Q", "M"), ("G", "M"), ("G", "Q")):
    deltas = [total(r, first) - total(r, second) for r in rows]
    low, high = bootstrap_ci(deltas)
    print(f"  {first} vs {second}: mean={statistics.mean(deltas):.2f} [{low:.2f}, {high:.2f}], "
          f"SD={statistics.stdev(deltas):.2f}, min={min(deltas):.2f}, max={max(deltas):.2f}, "
          f"mean |delta|={statistics.mean(abs(d) for d in deltas):.2f}")

print("\nQwen3.6 vs Gemma4, paired per submission (error = model total - human total):")
abs_gap = [abs(total(r, "G") - total(r, "M")) - abs(total(r, "Q") - total(r, "M")) for r in rows]
sq_gap = [(total(r, "G") - total(r, "M")) ** 2 - (total(r, "Q") - total(r, "M")) ** 2 for r in rows]
low, high = bootstrap_ci(abs_gap)
print(f"  |error| Gemma - Qwen: mean={statistics.mean(abs_gap):.2f} [{low:.2f}, {high:.2f}], "
      f"sign-flip p={sign_flip_p(abs_gap):.3f}; Qwen closer in {sum(g > 1e-9 for g in abs_gap)}, "
      f"Gemma closer in {sum(g < -1e-9 for g in abs_gap)}, tie in {sum(abs(g) <= 1e-9 for g in abs_gap)}")
low, high = bootstrap_ci(sq_gap)
print(f"  squared error Gemma - Qwen (MSE gap): mean={statistics.mean(sq_gap):.2f} [{low:.2f}, {high:.2f}], "
      f"sign-flip p={sign_flip_p(sq_gap):.3f}")

print("\nPer-question agreement with the human grader (model - human, missing entries left out):")
for grader in ("Q", "G"):
    print(f"  {GRADERS[grader]}:")
    for i in range(1, NUM_QUESTIONS + 1):
        pairs = [(r[f"M{i}"], r[f"{grader}{i}"]) for r in rows if r[f"{grader}{i}"] is not None]
        diffs = [g - m for m, g in pairs]
        corr = calculate_correlation([m for m, _ in pairs], [g for _, g in pairs])
        print(f"    Q{i}: r={corr:.2f}, mean diff={statistics.mean(diffs):+.2f}, "
              f"mean |diff|={statistics.mean(abs(d) for d in diffs):.2f}, n={len(pairs)}")

print("\nRe-run submissions (temperature 0.05) vs the rest (temperature 0):")
with open(CSV_PATH, encoding="utf-8", newline="") as f:
    temperatures = [(float(r["temperature_qwen"]), float(r["temperature_gemma"])) for r in csv.DictReader(f)]
for grader, column in (("Q", 0), ("G", 1)):
    deltas = [total(r, grader) - total(r, "M") for r in rows]
    rerun = [d for d, t in zip(deltas, temperatures) if t[column] > 0]
    rest = [d for d, t in zip(deltas, temperatures) if t[column] == 0]
    print(f"  {GRADERS[grader]}: re-run n={len(rerun)} mean diff={statistics.mean(rerun):.2f} "
          f"MSE={statistics.mean(d * d for d in rerun):.2f}; rest n={len(rest)} mean diff={statistics.mean(rest):.2f} "
          f"MSE={statistics.mean(d * d for d in rest):.2f}; permutation p={group_permutation_p(rerun, rest):.2f}; "
          f"without re-run: mean diff={statistics.mean(rest):.2f}, MSE={statistics.mean(d * d for d in rest):.2f}")
