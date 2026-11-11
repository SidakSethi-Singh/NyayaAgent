"""NyayaAgent config — LLM provider switch (no code change per provider).

Default is "offline": the agent drafts answers from verified corpus chunks
only, with no LLM call at all. That is the honest demo default — it cannot
hallucinate a section number because it can only quote the corpus.
Set NYAYA_LLM_PROVIDER=gemini|spark|ollama|nim to plug an LLM in as the
*drafter*; the verifier still gates every claim, and the LLM never invents
citations (see verifier.py).
"""
import os

LLM_PROVIDER = os.environ.get("NYAYA_LLM_PROVIDER", "offline").lower()
MAX_LOOPS = int(os.environ.get("NYAYA_MAX_LOOPS", "3"))
TOP_K = int(os.environ.get("NYAYA_TOP_K", "4"))
GROUNDING_THRESHOLD = float(os.environ.get("NYAYA_GROUNDING_THRESHOLD", "0.6"))
# Minimum BM25 score of the best retrieved chunk for an answer to be given.
# Calibrated on the 18-question benchmark (2026-11-11): every real question
# scores >= 13.17, the out-of-corpus trap ("own land on the Moon") scores
# 4.22. Below this floor the agent refuses instead of stretching a weak,
# generic chunk into an answer about a topic the corpus does not cover.
MIN_EVIDENCE_SCORE = float(os.environ.get("NYAYA_MIN_EVIDENCE_SCORE", "8.0"))

DISCLAIMER_EN = "Legal information, not legal advice. Verify with a lawyer for your case."
DISCLAIMER_HI = "यह कानूनी जानकारी है, कानूनी सलाह नहीं। अपने मामले के लिए वकील से ज़रूर सलाह लें।"
DISCLAIMER_HINGLISH = "Ye kanooni jaankari hai, kanooni salah nahi. Apne mamle ke liye vakil se zaroor salah lein."
