"""
Standalone Evaluation Script for Project Compass RAG Pipeline.

Evaluates 3-Category Performance:
1. Specific Factual (Path A: High Precision Chunk Matching)
2. Broad Summary (Path B: Document Overview & Architecture Summary)
3. Unanswerable / Cross-Tenant (Dual-Path Refusal Gate)

Metrics:
- Retrieval Hit-Rate@K
- Mean Reciprocal Rank (MRR@K)
- Grounded Answer Correctness
- Dual-Path Routing Precision (Path A vs Path B)
- Security & Anti-Hallucination Refusal Accuracy Gate
- Latency statistics (Retrieval, Rerank, Generation)

Usage:
    python evaluate.py [--mock-llm] [--eval-file eval_set.json]
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "compass_project.settings")

import django
django.setup()

from compass.services.evaluation import run_evaluation


def main():
    parser = argparse.ArgumentParser(description="Evaluate Project Compass RAG Retrieval and Dual-Path Performance")
    parser.add_argument(
        "--eval-file",
        type=str,
        default="eval_set.json",
        help="Path to evaluation benchmark JSON file (default: eval_set.json)"
    )
    parser.add_argument(
        "--mock-llm",
        action="store_true",
        default=True,
        help="Use mock LLM responses for quick headless verification of retrieval hit-rate and refusal gates"
    )
    args = parser.parse_args()

    eval_path = args.eval_file
    if not os.path.isabs(eval_path):
        eval_path = os.path.join(BASE_DIR, eval_path)

    if not os.path.exists(eval_path):
        print(f"Error: Evaluation benchmark file not found at: {eval_path}")
        sys.exit(1)

    print("\n==========================================================================================")
    print("               PROJECT COMPASS — DUAL-PATH RAG EVALUATION HARNESS                         ")
    print("==========================================================================================\n")
    print(f"Benchmark file: {eval_path}")
    print(f"Mode          : {'Fast Headless Mode (Mock LLM)' if args.mock_llm else 'Live Ollama Generation'}\n")

    report = run_evaluation(benchmark_path=eval_path, mock_llm=args.mock_llm)

    header = f"{'Case ID':<30} {'Category':<18} {'Path':<10} {'Hit?':<6} {'Outcome':<18} {'Latency':<8}"
    print(header)
    print("-" * len(header))

    for c in report.case_results:
        hit_str = "YES" if c.hit else ("-" if c.expected_refusal else "NO")
        path_str = c.actual_path.upper() if c.actual_path else "-"
        if c.expected_refusal:
            outcome = "REFUSED (OK)" if c.actual_refusal else "UNREFUSED (LEAK)"
        else:
            outcome = "CORRECT" if c.answer_correct else "MISSED/REFUSED"

        print(f"{c.case_id:<30} {c.category:<18} {path_str:<10} {hit_str:<6} {outcome:<18} {c.latency_ms:.0f}ms")

    print("-" * len(header))
    print("\nKEY PERFORMANCE METRICS (KPIs):")
    print(f"  • Total Test Cases               : {report.total_cases}")
    print(f"  • Grounded Retrieval Cases       : {report.grounded_cases}")
    print(f"    - Specific Factual (Path A)    : {report.specific_factual_correct}/{report.specific_factual_cases} correct ({report.specific_factual_correct / max(report.specific_factual_cases, 1) * 100:.1f}%)")
    print(f"    - Broad Summary (Path B)       : {report.broad_summary_correct}/{report.broad_summary_cases} correct ({report.broad_summary_correct / max(report.broad_summary_cases, 1) * 100:.1f}%)")
    print(f"  • Dual-Path Refusal Cases        : {report.refusal_cases}")
    print(f"  • Retrieval Hit-Rate@K           : {report.retrieval_hit_rate * 100:.1f}% (Target: >= 90%)")
    print(f"  • Mean Reciprocal Rank (MRR@K)   : {report.mrr_at_k:.3f}")
<<<<<<< HEAD
    print(f"  • Precision@K (Candidate Set)    : {report.precision_at_k * 100:.1f}%")
    print(f"  • Recall@K                       : {report.recall_at_k * 100:.1f}%")
    print(f"  • Grounded Answer Correctness    : {report.answer_correctness_rate * 100:.1f}% (Target: >= 80%)")
=======
>>>>>>> cff9f62cc6728b15d39ff413ba5cfff7a681f894
    print(f"  • Refusal Gate Accuracy          : {report.refusal_accuracy * 100:.1f}% (Target: >= 90%)")
    print(f"  • Average Total Latency          : {report.average_latency_ms:.1f} ms")

    print("\n" + "=" * 60)
    if report.passed:
        print("  [SUCCESS] All enterprise Dual-Path RAG thresholds met or exceeded!")
    else:
        print("  [FAIL] Did not meet target threshold.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
