#!/usr/bin/env python
"""
Eval runner — orchestrates the agent harness + graders and writes results.

Usage:
  uv run benchmarks/runners/eval_runner.py \\
    --benchmark lab_bench_protocol_qa \\
    --provider anthropic \\
    --model claude-sonnet-4-6 \\
    --max-items 50 \\
    --output benchmarks/results/

Benchmark choices:
  lab_bench_protocol_qa | lab_bench_litqa2 | bioprobench |
  internal_eln | internal_controls | internal_citations | internal_troubleshooting | all
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Project root so we can import eln.*
_REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

BENCHMARKS_DIR = Path(__file__).parent.parent
RESULTS_DIR = BENCHMARKS_DIR / "results"
EXTERNAL_DIR = BENCHMARKS_DIR / "datasets" / "external"
INTERNAL_DIR = BENCHMARKS_DIR / "datasets" / "internal"

EXTERNAL_BENCHMARKS = {
    "lab_bench_protocol_qa": EXTERNAL_DIR / "lab_bench_protocol_qa.jsonl",
    "lab_bench_litqa2": EXTERNAL_DIR / "lab_bench_litqa2.jsonl",
    "bioprobench": EXTERNAL_DIR / "bioprobench_error_correction.jsonl",
}

INTERNAL_BENCHMARKS = {
    "internal_eln": INTERNAL_DIR / "eln_completeness",
    "internal_controls": INTERNAL_DIR / "controls",
    "internal_citations": INTERNAL_DIR / "citations",
    "internal_troubleshooting": INTERNAL_DIR / "troubleshooting",
}

ALL_BENCHMARKS = list(EXTERNAL_BENCHMARKS.keys()) + list(INTERNAL_BENCHMARKS.keys())


# ── Loaders ──────────────────────────────────────────────────────────────────

def load_external_items(path: Path, max_items: int | None) -> list[dict]:
    if not path.exists():
        print(f"  WARNING: {path} not found. Run download_datasets.py first.", file=sys.stderr)
        return []
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                row = json.loads(line)
                if row.get("_placeholder"):
                    print(f"  WARNING: {path.name} is a placeholder — dataset was not downloaded.", file=sys.stderr)
                    return []
                items.append(row)
    return items[:max_items] if max_items else items


def load_internal_items(directory: Path, max_items: int | None) -> list[dict]:
    if not directory.exists():
        print(f"  WARNING: {directory} not found.", file=sys.stderr)
        return []
    items = []
    for p in sorted(directory.glob("*.json")):
        with open(p) as f:
            items.append(json.load(f))
    return items[:max_items] if max_items else items


# ── Grading dispatch ──────────────────────────────────────────────────────────

def grade_item(benchmark: str, item: dict, result, judge_model=None) -> dict:
    """Route to the appropriate grader and return a score dict."""
    from benchmarks.graders import multiple_choice_grader, citation_grader, eln_grader, controls_grader

    scores: dict = {}

    if benchmark in ("lab_bench_protocol_qa", "lab_bench_litqa2", "bioprobench"):
        mcq = multiple_choice_grader.grade(result.response, item["answer"])
        scores = dataclasses.asdict(mcq)

    elif benchmark == "internal_eln":
        eln = eln_grader.grade(result.response)
        scores = dataclasses.asdict(eln)

    elif benchmark == "internal_controls":
        gold = item.get("gold", {})
        ctrl = controls_grader.grade(result.response, gold)
        scores = dataclasses.asdict(ctrl)

    elif benchmark == "internal_citations":
        cit = citation_grader.grade(result.response, result.citations)
        scores = dataclasses.asdict(cit)

    elif benchmark == "internal_troubleshooting":
        from benchmarks.graders import llm_judge
        judge = llm_judge.grade(item["prompt"], result.response, judge_model=judge_model)
        scores = dataclasses.asdict(judge)

    return scores


def aggregate_scores(benchmark: str, scored_items: list[dict]) -> dict:
    """Compute aggregate metrics across all scored items."""
    if not scored_items:
        return {"score": 0.0, "n": 0}

    if benchmark in ("lab_bench_protocol_qa", "lab_bench_litqa2", "bioprobench"):
        correct = sum(1 for s in scored_items if s.get("scores", {}).get("correct", False))
        return {"accuracy": correct / len(scored_items), "correct": correct, "n": len(scored_items)}

    elif benchmark == "internal_eln":
        avg = sum(s.get("scores", {}).get("score", 0) for s in scored_items) / len(scored_items)
        return {"avg_score": round(avg, 2), "n": len(scored_items)}

    elif benchmark == "internal_controls":
        avg_f1 = sum(s.get("scores", {}).get("f1", 0) for s in scored_items) / len(scored_items)
        avg_recall = sum(s.get("scores", {}).get("recall", 0) for s in scored_items) / len(scored_items)
        return {"avg_f1": round(avg_f1, 4), "avg_recall": round(avg_recall, 4), "n": len(scored_items)}

    elif benchmark == "internal_citations":
        avg = sum(s.get("scores", {}).get("score", 0) for s in scored_items) / len(scored_items)
        return {"avg_score": round(avg, 4), "n": len(scored_items)}

    elif benchmark == "internal_troubleshooting":
        avg = sum(s.get("scores", {}).get("total", 0) for s in scored_items) / len(scored_items)
        return {"avg_rubric_total": round(avg, 2), "max_possible": 10, "n": len(scored_items)}

    return {"n": len(scored_items)}


# ── Main runner ───────────────────────────────────────────────────────────────

def run_benchmark(
    benchmark: str,
    provider: str,
    model: str,
    max_items: int | None,
    output_dir: Path,
    judge_model=None,
    timeout_s: int = 120,
) -> dict:
    from benchmarks.runners.agent_harness import build_harness

    print(f"\n{'='*60}")
    print(f"Benchmark : {benchmark}")
    print(f"Provider  : {provider} / {model}")
    print(f"Max items : {max_items or 'all'}")
    print(f"{'='*60}\n")

    # Load items
    if benchmark in EXTERNAL_BENCHMARKS:
        items = load_external_items(EXTERNAL_BENCHMARKS[benchmark], max_items)
    else:
        items = load_internal_items(INTERNAL_BENCHMARKS[benchmark], max_items)

    if not items:
        print(f"  No items loaded for {benchmark}. Skipping.")
        return {"benchmark": benchmark, "provider": provider, "model": model, "n": 0}

    print(f"  Loaded {len(items)} items.\n")

    harness = build_harness(provider=provider, model_name=model, timeout_s=timeout_s)

    scored_items = []
    total_cost = 0.0
    t0 = time.monotonic()

    for i, item in enumerate(items, 1):
        item_id = item.get("id", f"item_{i}")
        prompt = item.get("prompt") or item.get("question", "")

        # For MCQ items, append choices to the prompt
        choices = item.get("choices")
        if choices:
            choice_text = "\n".join(f"  {k}. {v}" for k, v in sorted(choices.items()))
            prompt = f"{prompt}\n\nChoices:\n{choice_text}\n\nAnswer with the letter only."

        mode = item.get("mode", "normal")

        print(f"  [{i}/{len(items)}] {item_id} … ", end="", flush=True)
        result = harness.run(item_id=item_id, question=prompt, mode=mode)

        if result.error:
            print(f"ERROR: {result.error}")
        else:
            print(f"{result.latency_ms}ms")

        scores = grade_item(benchmark, item, result, judge_model=judge_model)
        total_cost += result.estimated_cost_usd

        scored_items.append({
            "item_id": item_id,
            "question": prompt[:200],
            "response": result.response[:500],
            "agent_route": result.agent_route,
            "latency_ms": result.latency_ms,
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "cost_usd": result.estimated_cost_usd,
            "error": result.error,
            "scores": scores,
        })

    elapsed = time.monotonic() - t0
    aggregate = aggregate_scores(benchmark, scored_items)

    run_record = {
        "benchmark": benchmark,
        "provider": provider,
        "model": model,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "elapsed_s": round(elapsed, 1),
        "total_cost_usd": round(total_cost, 4),
        "aggregate": aggregate,
        "items": scored_items,
    }

    # Save per-run JSON
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_path = output_dir / f"{benchmark}_{provider}_{model.replace('/', '-')}_{ts}.json"
    with open(out_path, "w") as f:
        json.dump(run_record, f, indent=2)
    print(f"\n  Results saved: {out_path}")
    print(f"  Aggregate: {aggregate}")
    print(f"  Total cost: ${total_cost:.4f}")

    return run_record


def update_summary(results: list[dict], output_dir: Path) -> None:
    """Regenerate results/summary.md with a leaderboard table."""
    summary_path = output_dir / "summary.md"

    # Load existing non-current results from existing summary if present
    existing_rows: list[dict] = []
    if summary_path.exists():
        # We just rebuild from scratch — the JSON files are authoritative
        pass

    # Collect all JSON result files
    all_records: list[dict] = list(results)
    for p in sorted(output_dir.glob("*.json")):
        try:
            with open(p) as f:
                rec = json.load(f)
            # Avoid duplicates by checking if already in results
            sig = (rec.get("benchmark"), rec.get("provider"), rec.get("model"), rec.get("timestamp"))
            if not any(
                (r.get("benchmark"), r.get("provider"), r.get("model"), r.get("timestamp")) == sig
                for r in all_records
            ):
                all_records.append(rec)
        except Exception:
            pass

    # Sort by benchmark, then by score descending
    def _sort_key(r):
        agg = r.get("aggregate", {})
        score = agg.get("accuracy") or agg.get("avg_score") or agg.get("avg_f1") or agg.get("avg_rubric_total") or 0
        return (r.get("benchmark", ""), -float(score))

    all_records.sort(key=_sort_key)

    lines = [
        "# ELN++ Benchmark Leaderboard",
        "",
        f"_Last updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        "| Benchmark | Provider | Model | Score | Items | Cost |",
        "|-----------|----------|-------|-------|-------|------|",
    ]

    for rec in all_records:
        agg = rec.get("aggregate", {})
        score_val = (
            agg.get("accuracy")
            or agg.get("avg_score")
            or agg.get("avg_f1")
            or agg.get("avg_rubric_total")
            or 0
        )
        if "accuracy" in agg:
            score_str = f"{score_val*100:.1f}%"
        elif "avg_rubric_total" in agg:
            score_str = f"{score_val:.1f}/{agg['max_possible']}"
        else:
            score_str = f"{score_val:.2f}"

        n = agg.get("n", rec.get("n", "—"))
        cost = rec.get("total_cost_usd", 0)
        lines.append(
            f"| {rec.get('benchmark','')} | {rec.get('provider','')} | {rec.get('model','')} "
            f"| {score_str} | {n} | ${cost:.4f} |"
        )

    # Reference rows from published baselines
    lines += [
        "| LAB-Bench LitQA2 (human) | — | — | ~85% | — | reference |",
        "| LAB-Bench ProtocolQA (human) | — | — | ~72% | — | reference |",
        "| FutureHouse PaperQA2 | — | — | ~90% | — | reference |",
        "",
        "## Notes",
        "- Human baselines from the LAB-Bench paper (Laurent et al., 2024).",
        "- FutureHouse PaperQA2 score from the original PaperQA2 paper.",
        "- Internal benchmarks (ELN, Controls, Citations, Troubleshooting) have no external baseline.",
        "- Cost estimates based on published API pricing; actual costs may differ.",
    ]

    with open(summary_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\nLeaderboard updated: {summary_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ELN++ Eval Runner")
    parser.add_argument(
        "--benchmark",
        nargs="+",
        choices=ALL_BENCHMARKS + ["all"],
        default=["all"],
        help="Benchmark(s) to run",
    )
    parser.add_argument(
        "--provider",
        nargs="+",
        choices=["anthropic", "openai", "gemini"],
        default=["anthropic"],
        help="LLM provider(s)",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Model name (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Max items per benchmark (default: all)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=RESULTS_DIR,
        help="Output directory for result JSON files",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Per-item timeout in seconds (default: 120)",
    )
    args = parser.parse_args()

    benchmarks = ALL_BENCHMARKS if "all" in args.benchmark else args.benchmark

    all_results = []
    for provider in args.provider:
        for benchmark in benchmarks:
            record = run_benchmark(
                benchmark=benchmark,
                provider=provider,
                model=args.model,
                max_items=args.max_items,
                output_dir=args.output,
                timeout_s=args.timeout,
            )
            all_results.append(record)

    update_summary(all_results, args.output)
    print("\nAll done.")


if __name__ == "__main__":
    main()
