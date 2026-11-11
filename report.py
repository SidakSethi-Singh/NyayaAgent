"""report.py — AgentProof-style model card / eval report from results.jsonl."""
import json
from collections import Counter
from pathlib import Path


def build_report(results_path: str = "results/results.jsonl",
                 out_path: str = "results/eval_report.md") -> str:
    rows = [json.loads(l) for l in Path(results_path).read_text(encoding="utf-8").splitlines()
            if l.strip()] if Path(results_path).exists() else []
    if not rows:
        return "No eval results yet — run: python3 -m unittest discover -s tests, then ask questions via agent.py."
    n = len(rows)
    refused = sum(1 for r in rows if r["refused"])
    answered = [r for r in rows if not r["refused"]]
    # Groundedness / citation coverage are meaningless on refusals (0.0 by
    # design), so average them over answered questions only.
    avg = {k: round(sum(r["scores"].get(k, 0) for r in answered) / max(len(answered), 1), 2)
           for k in ("groundedness", "citation_coverage")}
    avg["refusal_correctness"] = round(sum(r["scores"].get("refusal_correctness", 0)
                                           for r in rows) / n, 2)
    avg["language_match"] = round(sum(r["scores"].get("language_match", 0)
                                      for r in rows) / n, 2)
    passed = sum(1 for r in rows if r["scores"].get("passed"))
    md = ("# NyayaAgent — Eval Report\n\n"
          f"Questions asked: {n} · Refused: {refused} · Passed gates: {passed}/{n}\n\n"
          "## Average scores\n\n" +
          "".join(f"- {k}: {v}\n" for k, v in avg.items()) +
          "\n## Failures (honest list)\n\n" +
          "".join(f"- {r['question']} → refused={r['refused']}, scores={r['scores']}\n"
                  for r in rows if not r["scores"].get("passed")) +
          "\n_Legal information, not legal advice._\n")
    Path(out_path).write_text(md, encoding="utf-8")
    return md


if __name__ == "__main__":
    print(build_report())
