"""Reproducible eval: run every question in data/benchmark.jsonl through
ask(), log to results/results.jsonl, rebuild results/eval_report.md.

Usage: python3 eval_run.py
Scores printed here are the only numbers the README may quote.
"""
import json
from pathlib import Path

from agent import ask
from report import build_report

ROOT = Path(__file__).parent


def main():
    bench = [json.loads(l) for l in (ROOT / "data" / "benchmark.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    log = ROOT / "results" / "results.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    if log.exists():
        log.unlink()
    rows = []
    for b in bench:
        r = ask(b["question"], log_path=log)
        ok = r["scores"]["passed"]
        # A trap must be refused; a non-trap must be answered and pass gates.
        expected_ok = (r["refused"] if b["trap"] else (not r["refused"] and ok))
        rows.append((b, r, expected_ok))
        print(f"{'TRAP ' if b['trap'] else '     '} {'OK  ' if expected_ok else 'FAIL'} "
              f"refused={r['refused']} passed={r['scores']['passed']} "
              f"g={r['scores']['groundedness']} cit={r['scores']['citation_coverage']} "
              f"ref={r['scores']['refusal_correctness']} lang={r['scores']['language_match']} "
              f"| {b['question'][:70]}")
        if r.get("checker_problems"):
            print("   CHECKER:", r["checker_problems"])
    n = len(rows)
    passed = sum(1 for _, r, _ in rows if r["scores"]["passed"])
    exp_ok = sum(1 for _, _, e in rows if e)
    print(f"\n{exp_ok}/{n} match expected behaviour (trap refused / non-trap answered+passed); "
          f"{passed}/{n} passed evaluator gates.")
    print(build_report())


if __name__ == "__main__":
    main()
