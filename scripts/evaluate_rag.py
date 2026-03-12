#!/usr/bin/env python3
"""CLI script for batch RAG evaluation using Ragas.

Usage:
    python scripts/evaluate_rag.py samples.jsonl
    python scripts/evaluate_rag.py samples.jsonl --output results.json

JSONL format (one JSON object per line):
    {"question": "...", "answer": "...", "contexts": ["..."], "ground_truth": "..."}
"""

import argparse
import json
import sys

import httpx


def main():
    parser = argparse.ArgumentParser(description="Batch RAG evaluation via Ragas")
    parser.add_argument("input_file", help="Path to JSONL file with eval samples")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000/ai/eval/evaluate",
        help="Evaluation API endpoint URL",
    )
    parser.add_argument("--timeout", type=int, default=300, help="Request timeout in seconds")
    args = parser.parse_args()

    # Read JSONL
    samples = []
    with open(args.input_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                samples.append({
                    "question": obj["question"],
                    "answer": obj["answer"],
                    "contexts": obj.get("contexts", []),
                    "ground_truth": obj.get("ground_truth", ""),
                })
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Skipping line {line_num}: {e}", file=sys.stderr)

    if not samples:
        print("Error: No valid samples found in input file.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(samples)} samples from {args.input_file}", file=sys.stderr)

    # Call evaluation endpoint
    try:
        with httpx.Client(timeout=args.timeout) as client:
            resp = client.post(args.api_url, json={"samples": samples})
            resp.raise_for_status()
            result = resp.json()
    except httpx.HTTPError as e:
        print(f"Error calling evaluation API: {e}", file=sys.stderr)
        sys.exit(1)

    # Output results
    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output_json)

    # Print summary
    scores = result.get("scores", {})
    if scores:
        print("\n=== Evaluation Summary ===", file=sys.stderr)
        for metric, score in scores.items():
            print(f"  {metric}: {score:.4f}", file=sys.stderr)
    elif result.get("error"):
        print(f"\nEvaluation error: {result['error']}", file=sys.stderr)


if __name__ == "__main__":
    main()
