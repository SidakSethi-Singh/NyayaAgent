"""Tools the agent loop may call (spec §6).

In the offline MVP these are thin wrappers over the retriever/corpus.
With an LLM provider configured, the same tool names are what the LLM
calls — the verifier still gates the result either way.
"""
from retriever import BM25Retriever


def search_corpus(retriever: BM25Retriever, query: str, k: int = 4) -> list[dict]:
    return retriever.retrieve(query, k=k)


def get_section(retriever: BM25Retriever, act: str, section: str) -> dict | None:
    for c in retriever.corpus.chunks:
        if act.lower() in c["act"].lower() and section in c["section"]:
            return c
    return None


def get_case_summary(retriever: BM25Retriever, query: str) -> list[dict]:
    """MVP: case-law summaries live in the same corpus; no separate store yet."""
    return retriever.retrieve(query, k=2)
