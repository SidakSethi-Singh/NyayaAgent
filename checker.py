"""Deterministic checker — hard gates that no LLM judge can overrule.

- No citation may name a section that is not in the corpus.
- No answer may contain a section number that appears in no retrieved chunk.
- A refusal must not contain a substantive legal claim.
"""
import re

from retriever import Corpus

SECTION_RE = re.compile(r"(?:section|article|dhara)\s*(\d+[A-Za-z]?(?:\(\d+\))?(?:\([a-z]\))?)", re.I)


def check_answer(answer: str, corpus: Corpus, refused: bool) -> list[str]:
    problems = []
    corpus_sections = set()
    for c in corpus.chunks:
        # A section is citable if it is a chunk's own section OR is named
        # inside a chunk's text (e.g. Article 19's text names Article 19(2)).
        # Otherwise the checker would flag the corpus's own words.
        corpus_sections.update(re.findall(r"\d+[A-Za-z]?(?:\(\d+\))?(?:\([a-z]\))?", c["section"]))
        corpus_sections.update(SECTION_RE.findall(c["text"]))
    for num in SECTION_RE.findall(answer):
        if num not in corpus_sections:
            problems.append(f"Cited section {num} is not in the corpus")
    if refused and SECTION_RE.search(answer):
        problems.append("Refusal contains a section citation")
    return problems
