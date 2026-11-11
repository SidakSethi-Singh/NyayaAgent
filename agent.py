"""Agent loop — plan → retrieve → draft → verify → evaluate
→ [re-retrieve | answer | refuse]. Max 3 loops (config.MAX_LOOPS).

Offline MVP drafter: answers are assembled ONLY from verified corpus
chunks, in the user's language (English / Hindi / Hinglish). No LLM call,
so no hallucinated section can enter the answer — the verifier and the
deterministic checker are the gates, not a prompt.
"""
import json
import re
from pathlib import Path

from checker import check_answer
from config import (DISCLAIMER_EN, DISCLAIMER_HI, DISCLAIMER_HINGLISH,
                    GROUNDING_THRESHOLD, MAX_LOOPS, MIN_EVIDENCE_SCORE, TOP_K)
from evaluator import evaluate
from planner import plan
from retriever import load_retriever
from tools import search_corpus
from verifier import verify

_HI_TEMPLATES = {
    "intro": "इस सवाल का जवाब हमारे सत्यापित कॉर्पस के आधार पर है:",
    "refusal": ("इस सवाल के लिए हमारे कॉर्पस में पर्याप्त सत्यापित सबूत नहीं है। "
                "इसलिए मैं इसका जवाब नहीं दे सकता — गलत धारा बताने से बेहतर है "
                "यह कहना कि सबूत नहीं है।"),
    "missing": "क्या नहीं मिला: इस धारा या कानून पर कॉर्पस में कोई chunk नहीं है।",
}
_HINGLISH_TEMPLATES = {
    "intro": "Is sawal ka jawab hamare verified corpus ke aadhar par hai:",
    "refusal": ("Is sawal ke liye hamare corpus mein kaafi verified saboot nahi hai. "
                "Isliye main iska jawab nahi de sakta — galat section batane se behtar hai "
                "yeh kehna ki saboot nahi hai."),
    "missing": "Kya missing hai: is section ya kanoon par corpus mein koi chunk nahi mila.",
}
_EN_TEMPLATES = {
    "intro": "Here is the answer, based only on the verified corpus:",
    "refusal": ("I do not have enough verified evidence in the corpus for this question, "
                "so I will not answer it. Saying that is better than inventing a section."),
    "missing": "What is missing: no chunk in the corpus covers this section or law.",
}


def _sentences_from_chunks(chunks: list[dict], language: str) -> list[str]:
    """One claim sentence per chunk, quoting its act + section + summary.

    Hindi answers lead with the chunk's Hindi summary (hi_summary) so the
    answer reads in Hindi first; the English chunk text remains the cited
    source. Hinglish/English answers quote the English chunk text.
    """
    out = []
    for r in chunks:
        c = r["chunk"]
        if language == "hi":
            out.append(
                f"{c['act']} के {c['section']} के अनुसार — {c['title']}: "
                f"{c.get('hi_summary') or c['text']}")
        elif language == "hinglish":
            out.append(
                f"{c['act']} {c['section']} kehta hai — {c['title']}: {c['text']}")
        else:
            out.append(
                f"Under {c['section']} of the {c['act']} — {c['title']}: {c['text']}")
    return out


def _render(language: str, sentences: list[str], citations: list[dict],
            refused: bool, scores: dict) -> str:
    if language == "hi":
        t, disc = _HI_TEMPLATES, DISCLAIMER_HI
    elif language == "hinglish":
        t, disc = _HINGLISH_TEMPLATES, DISCLAIMER_HINGLISH
    else:
        t, disc = _EN_TEMPLATES, DISCLAIMER_EN
    if refused:
        body = t["refusal"] + "\n" + t["missing"]
    else:
        body = t["intro"] + "\n" + "\n".join(f"• {s}" for s in sentences)
        cites = "\n".join(
            f"[{i+1}] {c['act']}, {c['section']} — {c['source_url']}"
            for i, c in enumerate(citations))
        body += "\n\nSources:\n" + cites
    body += f"\n\nEvaluator scores: groundedness {scores['groundedness']}, "
    body += f"citation coverage {scores['citation_coverage']}, "
    body += f"refusal correctness {scores['refusal_correctness']}, "
    body += f"language match {scores['language_match']}."
    body += f"\n\n{disc}"
    return body


def ask(question: str, retriever=None, log_path: str | Path | None = None) -> dict:
    """Run the full loop. Returns the trace + answer + scores (JSON-serialisable)."""
    retriever = retriever or load_retriever()
    p = plan(question)
    language = p["language"]
    trace = {"question": question, "plan": p, "loops": []}

    # Trap gate (spec demo step 1): if the question cites a section number
    # that exists in NO corpus chunk, refuse immediately — never answer a
    # fake section by quoting a different, real one.
    cited_nums = set(re.findall(r"(?:section|article|dhara)\s*(\d+[A-Za-z]?(?:\(\d+\))?(?:\([a-z]\))?)",
                                question, re.I))
    corpus_nums = set()
    for c in retriever.corpus.chunks:
        corpus_nums.update(re.findall(r"\d+[A-Za-z]?(?:\(\d+\))?(?:\([a-z]\))?", c["section"]))
    fake_nums = cited_nums - corpus_nums
    # Case-name trap: the corpus contains statutes only, no case law. A
    # question citing a case ("Sharma v. State") is unverifiable here —
    # refuse it rather than inventing what the court held.
    case_cited = re.search(r"\b[A-Z][A-Za-z]+ v\.?\s+(?:the\s+)?[A-Z][A-Za-z]+", question)
    if case_cited:
        fake_nums = fake_nums or {"case"}
    if fake_nums:
        scores = {"groundedness": 0.0, "citation_coverage": 0.0,
                  "refusal_correctness": 1.0, "language_match": 1.0, "passed": True}
        from evaluator import language_match
        answer = _render(language, [], [], True, scores)
        scores["language_match"] = language_match(question, answer)
        answer = _render(language, [], [], True, scores)
        trap_note = ("Cited case is not in the corpus (the corpus holds statutes only, no case law)"
                     if "case" in fake_nums
                     else f"Cited section(s) {sorted(fake_nums)} not in corpus")
        trace.update({"answer": answer, "refused": True, "scores": scores,
                      "checker_problems": [],
                      "trap": trap_note})
        if log_path:
            Path(log_path).parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"question": question, "refused": True,
                                    "scores": scores}, ensure_ascii=False) + "\n")
        return trace

    chunks: list[dict] = []
    verification = {"supported": [], "unsupported": [], "groundedness": 0.0}
    best_score = 0.0

    for loop in range(1, MAX_LOOPS + 1):
        # Round-robin retrieval: one top chunk per query (question first,
        # then each sub-question in plan order), then fill remaining slots
        # by score. This keeps each retrieved chunk tied to a specific
        # sub-question instead of letting one generic query dominate.
        queries = ([question] + p["sub_questions"] if loop == 1
                   else p["sub_questions"])
        picked: list[dict] = []
        seen_keys: set[str] = set()
        best_by_key: dict[str, dict] = {}
        # Pass 1: run every query and keep each chunk's BEST score across
        # queries. (Scoring a chunk by the first query that found it kept
        # its weakest score — e.g. Section 106 scored 5.06 on the raw
        # question but 17.57 on its sub-question — and the evidence gate
        # then wrongly refused a good question.)
        all_hits: list[list[dict]] = []
        for q in queries:
            hits = search_corpus(retriever, q, k=TOP_K)
            all_hits.append(hits)
            for h in hits:
                key = h["chunk"]["act"] + h["chunk"]["section"]
                if key not in best_by_key or h["score"] > best_by_key[key]["score"]:
                    best_by_key[key] = h
        # Pass 2: one TOP-1 chunk per query, scored at its best across queries.
        for hits in all_hits:
            for h in hits:
                # Only a query's TOP-1 chunk counts for that query. If it is
                # already picked, the query adds nothing — taking its 2nd-best
                # is how generic chunks (Article 14) leaked into answers.
                key = h["chunk"]["act"] + h["chunk"]["section"]
                if key not in seen_keys:
                    seen_keys.add(key)
                    picked.append(best_by_key[key])
                break
        if len(picked) < TOP_K:
            # Fill only with chunks at least half as strong as the strongest
            # evidence seen in this loop — otherwise a generic chunk (e.g.
            # Article 14, which matches the word "law" in almost any query)
            # sneaks into every answer.
            ranked = list(best_by_key.values())
            fill_threshold = 0.5 * max(h["score"] for h in ranked) if ranked else 0.0
            for h in sorted(ranked, key=lambda x: x["score"], reverse=True):
                key = h["chunk"]["act"] + h["chunk"]["section"]
                if key not in seen_keys and h["score"] >= fill_threshold:
                    seen_keys.add(key)
                    picked.append(h)
                if len(picked) >= TOP_K:
                    break
        chunks = picked[:TOP_K]
        if chunks:
            best_score = max(best_score, max(h["score"] for h in chunks))
        sentences = _sentences_from_chunks(chunks, language)
        verification = verify(sentences, [r["chunk"] for r in chunks])
        trace["loops"].append({
            "loop": loop,
            "retrieved": [f"{r['chunk']['act']} {r['chunk']['section']} ({r['score']:.2f})"
                          for r in chunks],
            "groundedness": verification["groundedness"],
            "unsupported": verification["unsupported"],
        })
        if verification["groundedness"] >= GROUNDING_THRESHOLD or not chunks:
            break
        # Evidence weak: re-retrieve with the sub-questions as queries next loop.
        p["sub_questions"] = [s for s in p["sub_questions"]]

    # Evidence must be both grounded AND strong: a weak generic match
    # (e.g. BNS 351 for "own land on the Moon") is not evidence.
    evidence_found = (bool(chunks)
                      and verification["groundedness"] >= GROUNDING_THRESHOLD
                      and best_score >= MIN_EVIDENCE_SCORE)
    refused = not evidence_found
    supported = verification["supported"]
    sentences = [s["sentence"] for s in supported]
    citations = [s["citation"] for s in supported]
    scores = evaluate(question, "", verification, refused, evidence_found)
    answer = _render(language, sentences, citations, refused, scores)
    # Language match must be scored on the real answer, not the empty draft.
    from evaluator import language_match
    scores["language_match"] = language_match(question, answer)
    answer = _render(language, sentences, citations, refused, scores)
    problems = check_answer(answer, retriever.corpus, refused)
    if problems:
        # Hard gate failed: refuse rather than ship a bad citation.
        refused, scores = True, evaluate(question, "", verification, True, False)
        answer = _render(language, [], [], True, scores)
    trace.update({"answer": answer, "refused": refused, "scores": scores,
                  "checker_problems": problems})
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"question": question, "refused": refused,
                                "scores": scores}, ensure_ascii=False) + "\n")
    return trace


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "Makaan malik bina notice ke nikaal sakta hai kya?"
    result = ask(q, log_path="results/results.jsonl")
    print(result["answer"])
