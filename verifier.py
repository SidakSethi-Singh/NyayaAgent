"""Verifier — sentence-level grounding (the SlothClerk/Ofrenda pattern).

Every claim sentence in a draft must share content words with at least one
retrieved chunk, or quote a section that chunk actually contains. Unsupported
sentences are DROPPED, not polished. A draft with no supported claim is a
refusal, not an answer.
"""
import re

from retriever import tokenize

SECTION_RE = re.compile(r"(section|article|dhara)\s*(\d+[A-Za-z]?(?:\(\d+\))?(?:\([a-z]\))?)", re.I)


def claim_supported(claim: str, chunks: list[dict]) -> tuple[bool, dict | None]:
    """True + best chunk if the claim is grounded in any retrieved chunk."""
    claim_toks = set(tokenize(claim))
    if not claim_toks:
        return False, None
    # A cited section must exist in the chunk it is attributed to.
    cited = SECTION_RE.findall(claim)
    best, best_overlap = None, 0
    for c in chunks:
        chunk_toks = set(c["_tokens"])
        overlap = len(claim_toks & chunk_toks)
        if cited:
            cited_nums = {num for _, num in cited}
            chunk_nums = set(re.findall(r"\d+[A-Za-z]?(?:\(\d+\))?(?:\([a-z]\))?", c["section"]))
            if not (cited_nums & chunk_nums):
                continue  # claim cites a section this chunk does not contain
            if overlap >= 1:
                return True, c
        elif overlap > best_overlap:
            best, best_overlap = c, overlap
    if best is not None and best_overlap >= 2:
        return True, best
    return False, None


def verify(draft_sentences: list[str], chunks: list[dict]) -> dict:
    """Split a draft into supported / unsupported claims."""
    supported, unsupported = [], []
    for s in draft_sentences:
        ok, chunk = claim_supported(s, chunks)
        if ok:
            supported.append({"sentence": s, "citation": chunk})
        else:
            unsupported.append(s)
    total = len(draft_sentences)
    groundedness = len(supported) / total if total else 0.0
    return {"supported": supported, "unsupported": unsupported,
            "groundedness": groundedness}
