"""Retriever — hybrid BM25 over the curated corpus (pure Python, no deps).

BM25 is implemented here in ~60 lines so the MVP runs anywhere with no
install. The full-stack version swaps this for ChromaDB dense embeddings +
rank-bm25 re-ranking (see requirements.txt "full" extras); the interface
(top-k chunks with scores) stays the same, so the agent loop does not change.
"""
import json
import math
import re
from pathlib import Path

STOPWORDS = set("""a an the is are was were be been being of to in on at for with by
from as and or not no if then than this that these those it its he she they we you
i me my your his her their our what which who whom how when where why can could
should would may might must shall will do does did have has had kya hai hain ka ki
ke ko se mein me par bhi nahi""".split())
# Devanagari function words — without these, a common verb like हुआ ("happened")
# matches any chunk whose Hindi summary contains it, and generic chunks leak
# into Hindi answers (e.g. Contract Act 73 answering an online-fraud question).
STOPWORDS |= set("""है हैं क्या मुझे मैं मेरा मेरी मेरे तुम तुम्हारा वह यह ये वो को का की के से में
पर और या नहीं नही कैसे कब क्यों कहाँ किस किसका करूँ करूं करो करें सकता सकती सकते
चाहिए होगा होगी होंगे था थी थे जब तब तो भी ही सिर्फ बहुत कुछ कोई एक दो अपने अपना
अपनी मुझसे उसका उसकी उसके इसका इसकी इसके हम हमारा हमारी हमारे तुम्हें उसे उन्हें
इसे इन्हें जिन्हें जिनका जिसका जिसके जिसकी हुआ हुई हुए करना करने किया जाता है""".split())

TOKEN_RE = re.compile(r"[a-z0-9\u0900-\u097F]+")


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


class Corpus:
    def __init__(self, path: str | Path):
        self.chunks = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()
                       if line.strip()]
        for c in self.chunks:
            # hi_summary is tokenised too, so Devanagari questions match the
            # Hindi summary of a chunk, not only its English text.
            c["_tokens"] = tokenize(c["act"] + " " + c["section"] + " " + c["title"]
                                    + " " + c["text"] + " " + c.get("hi_summary", ""))

    def __len__(self):
        return len(self.chunks)


class BM25Retriever:
    """Classic BM25 (k1=1.5, b=0.75) over corpus chunks."""

    def __init__(self, corpus: Corpus):
        self.corpus = corpus
        self.n = len(corpus.chunks)
        self.avgdl = sum(len(c["_tokens"]) for c in corpus.chunks) / max(self.n, 1)
        self.df: dict[str, int] = {}
        for c in corpus.chunks:
            for tok in set(c["_tokens"]):
                self.df[tok] = self.df.get(tok, 0) + 1

    def _idf(self, tok: str) -> float:
        df = self.df.get(tok, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def score(self, query: str, chunk: dict) -> float:
        qtok = tokenize(query)
        dl = len(chunk["_tokens"])
        total = 0.0
        for tok in qtok:
            f = chunk["_tokens"].count(tok)
            if not f:
                continue
            total += self._idf(tok) * (f * 2.5) / (f + 1.5 * (1 - 0.75 + 0.75 * dl / self.avgdl))
        # Exact section-number match is a strong signal (and a trap detector:
        # a fake section scores ~0 because no chunk contains it).
        if re.search(r"\b\d{2,3}\b", query):
            for num in re.findall(r"\b\d{2,3}\b", query):
                if num in chunk["section"]:
                    total += 5.0
        return total

    def retrieve(self, query: str, k: int = 4) -> list[dict]:
        scored = sorted(
            ({"chunk": c, "score": self.score(query, c)} for c in self.corpus.chunks),
            key=lambda x: x["score"], reverse=True)
        return [s for s in scored if s["score"] > 0][:k]


def load_retriever(corpus_path: str | Path = "data/corpus.jsonl") -> BM25Retriever:
    base = Path(__file__).parent
    path = base / corpus_path if not Path(corpus_path).is_absolute() else Path(corpus_path)
    return BM25Retriever(Corpus(path))
