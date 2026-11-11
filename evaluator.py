"""Evaluator — AgentProof-style scoring (deterministic checker = hard gate,
LLM judge = soft score, not implemented in the offline MVP).

Scores per answer:
- groundedness: share of claim sentences verified against retrieved chunks
- citation_coverage: share of supported claims that carry a citation
- refusal_correctness: 1.0 when the agent refused a question with no evidence,
  0.0 when it answered one (or refused one it could have answered)
- language_match: 1.0 when the answer language matches the question language
"""
import re

from config import GROUNDING_THRESHOLD


def language_match(question: str, answer: str) -> float:
    q_dev = bool(re.search(r"[\u0900-\u097F]", question))
    a_dev = bool(re.search(r"[\u0900-\u097F]", answer))
    return 1.0 if q_dev == a_dev else 0.5


def evaluate(question: str, answer: str, verification: dict, refused: bool,
             evidence_found: bool) -> dict:
    groundedness = verification.get("groundedness", 0.0)
    supported = verification.get("supported", [])
    citation_coverage = (len([s for s in supported if s.get("citation")]) / len(supported)
                         if supported else 0.0)
    if refused:
        refusal_correctness = 1.0 if not evidence_found else 0.0
    else:
        refusal_correctness = 1.0 if evidence_found else 0.0
    scores = {
        "groundedness": round(groundedness, 2),
        "citation_coverage": round(citation_coverage, 2),
        "refusal_correctness": refusal_correctness,
        "language_match": language_match(question, answer),
    }
    scores["passed"] = bool(
        (refused and refusal_correctness == 1.0)
        or (not refused and groundedness >= GROUNDING_THRESHOLD
            and citation_coverage >= 0.5))
    return scores
