#!/usr/bin/env python
"""
Download external benchmark datasets from HuggingFace and save as JSONL.

Datasets:
  - futurehouse/lab-bench  (ProtocolQA + LitQA2 splits)
  - chem-benchmarks/bioprobench (error-correction task)

Each row normalised to:
  { "id", "question", "choices" (if MCQ), "answer", "source" }

Usage:
  uv run benchmarks/runners/download_datasets.py
  uv run benchmarks/runners/download_datasets.py --datasets lab_bench_protocol_qa lab_bench_litqa2
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EXTERNAL_DIR = Path(__file__).parent.parent / "datasets" / "external"

DATASET_CONFIGS = {
    "lab_bench_protocol_qa": {
        "hf_name": "futurehouse/lab-bench",
        "split": "ProtocolQA",
        "output_file": "lab_bench_protocol_qa.jsonl",
    },
    "lab_bench_litqa2": {
        "hf_name": "futurehouse/lab-bench",
        "split": "LitQA2",
        "output_file": "lab_bench_litqa2.jsonl",
    },
    "bioprobench_error_correction": {
        "hf_name": "chem-benchmarks/bioprobench",
        "split": "error_correction",
        "output_file": "bioprobench_error_correction.jsonl",
        "fallback_hf_name": "futurehouse/lab-bench",  # fallback if primary unavailable
    },
}


def _normalise_lab_bench_row(row: dict, source: str, idx: int) -> dict:
    """Normalise a LAB-Bench row to common schema."""
    # LAB-Bench rows have: question, ideal, distractor1..3 (MCQ) or free-form
    choices = None
    answer = row.get("ideal", row.get("answer", ""))

    if all(f"distractor{i}" in row for i in range(1, 4)):
        # Build choices list: ideal + distractors, then sort alphabetically
        options = [str(answer), str(row["distractor1"]), str(row["distractor2"]), str(row["distractor3"])]
        options_sorted = sorted(set(options))  # deduplicate
        letters = "ABCD"
        choices = {letters[i]: opt for i, opt in enumerate(options_sorted[:4])}
        # Find which letter maps to the ideal answer
        answer_letter = next((k for k, v in choices.items() if v == str(answer)), "A")
        answer = answer_letter

    return {
        "id": row.get("id", f"{source}_{idx}"),
        "question": str(row.get("question", row.get("prompt", ""))),
        "choices": choices,
        "answer": str(answer),
        "source": source,
    }


def _normalise_bioprobench_row(row: dict, idx: int) -> dict:
    """Normalise a BioProBench row to common schema."""
    choices = None
    if "options" in row and isinstance(row["options"], (list, dict)):
        opts = row["options"]
        if isinstance(opts, list):
            letters = "ABCD"
            choices = {letters[i]: str(o) for i, o in enumerate(opts[:4])}
        else:
            choices = {str(k): str(v) for k, v in list(opts.items())[:4]}

    return {
        "id": row.get("id", f"bioprobench_{idx}"),
        "question": str(row.get("question", row.get("input", ""))),
        "choices": choices,
        "answer": str(row.get("answer", row.get("correct_option", "A"))),
        "source": "bioprobench",
    }


def download_dataset(name: str, config: dict, force: bool = False) -> Path:
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        print("ERROR: 'datasets' package not installed. Run: uv sync --extra bench", file=sys.stderr)
        sys.exit(1)

    out_path = EXTERNAL_DIR / config["output_file"]
    if out_path.exists() and not force:
        print(f"  {name}: already exists at {out_path} (use --force to re-download)")
        return out_path

    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)

    hf_name = config["hf_name"]
    split_name = config.get("split", "train")
    print(f"  {name}: downloading {hf_name} / {split_name} …")

    try:
        ds = load_dataset(hf_name, split=split_name, trust_remote_code=True)
    except Exception as e:
        fallback = config.get("fallback_hf_name")
        if fallback and fallback != hf_name:
            print(f"    Primary failed ({e}), trying fallback {fallback} …")
            try:
                ds = load_dataset(fallback, split=split_name, trust_remote_code=True)
                hf_name = fallback
            except Exception as e2:
                print(f"    Fallback also failed: {e2}")
                _write_placeholder(out_path, name, str(e))
                return out_path
        else:
            print(f"    Download failed: {e}")
            _write_placeholder(out_path, name, str(e))
            return out_path

    rows = []
    for idx, row in enumerate(ds):
        row_dict = dict(row)
        if "bioprobench" in hf_name:
            normalised = _normalise_bioprobench_row(row_dict, idx)
        else:
            normalised = _normalise_lab_bench_row(row_dict, name, idx)
        rows.append(normalised)

    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    print(f"    → saved {len(rows)} rows to {out_path}")
    return out_path


def _write_placeholder(path: Path, name: str, error: str) -> None:
    """Write a placeholder JSONL with one row explaining the download failure."""
    path.parent.mkdir(parents=True, exist_ok=True)
    placeholder = {
        "id": "placeholder_0",
        "question": f"[Dataset '{name}' unavailable — {error}]",
        "choices": None,
        "answer": "A",
        "source": name,
        "_placeholder": True,
    }
    with open(path, "w") as f:
        f.write(json.dumps(placeholder) + "\n")
    print(f"    → wrote placeholder to {path}")


def main():
    parser = argparse.ArgumentParser(description="Download benchmark datasets from HuggingFace")
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=list(DATASET_CONFIGS.keys()) + ["all"],
        default=["all"],
        help="Which datasets to download (default: all)",
    )
    parser.add_argument("--force", action="store_true", help="Re-download even if file exists")
    args = parser.parse_args()

    targets = list(DATASET_CONFIGS.keys()) if "all" in args.datasets else args.datasets

    print(f"Downloading {len(targets)} dataset(s) to {EXTERNAL_DIR}:\n")
    for name in targets:
        download_dataset(name, DATASET_CONFIGS[name], force=args.force)

    print("\nDone.")


if __name__ == "__main__":
    main()
