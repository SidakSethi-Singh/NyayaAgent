# NyayaAgent — Autonomous Agentic RAG for Indian Legal Questions

> Not a chatbot that answers once. An agent that plans, retrieves, verifies,
> and grades itself — before it dares to answer an Indian legal question —
> and shows you every citation it used.

**Hackathon project 2 of 2 — ML.ai INFRASHIFT, Sat 14 Nov 2026, Janakpuri West,
New Delhi · Track: Open Innovation · Built on Sid's own LawSathi + AgentProof.**

## The loop (LangGraph-style, pure Python in the MVP)

```
Question (EN / Hindi / Hinglish)
  → PLANNER: 2–4 sub-questions (EN + Devanagari keywords, 17 topics)
  → RETRIEVER: BM25 over a curated corpus (ChromaDB dense + rank-bm25 in "full")
  → DRAFTER (offline): answers assembled ONLY from retrieved chunks
  → VERIFIER: every claim must be grounded in a chunk; unsupported = dropped
  → EVALUATOR: groundedness, citation coverage, refusal correctness, language match
  → ANSWER or REFUSE (max 3 re-retrieve loops)
```

Three hard gates, none of which a prompt can overrule:

1. **Fake-section trap:** a question citing a section in no chunk (e.g. "BNS
   Section 999") is refused immediately — never answered by quoting a
   different, real section.
2. **Fake-case trap:** the corpus holds statutes only, no case law. A question
   citing a case ("Sharma v. State of Delhi 2024") is refused.
3. **Evidence-strength floor:** the best retrieved chunk must score ≥ 8.0
   (BM25). Calibrated on the benchmark: every real question scores ≥ 13.17,
   the out-of-corpus trap ("own land on the Moon") scores 4.22 — so a weak,
   generic match is refused instead of stretched into an answer.
4. **Deterministic checker** (`checker.py`): no citation may name a section
   absent from the corpus; a refusal must not contain a section citation.
   If it fails, the agent refuses rather than shipping a bad citation.

## Measured results (run 11 Nov 2026 — `python3 eval_run.py`)

- **Corpus: 71 chunks across 22 Acts** (tenancy, consumer, cyber, cheque
  bounce, divorce/maintenance, motor accident, RTI, DPDP, employment,
  property registration, FIR/bail, defamation, GST/tax, will/succession…)
- **Eval: 18 questions, 18/18 passed evaluator gates, 18/18 matched expected
  behaviour** — 15 answered, 3 traps refused (fake section, fake case,
  out-of-corpus topic)
- Average scores: groundedness **1.0**, citation coverage **1.0**,
  refusal correctness **1.0**, language match **1.0**
  (`results/eval_report.md`, rebuilt by `eval_run.py` from real runs)
- **Tests: 17/17 pass** (`python3 -m unittest discover -s tests -v`)

## Run it (no install for the CLI, no API key)

```bash
python3 agent.py "Makaan malik bina notice ke nikaal sakta hai kya?"
python3 agent.py "BNS Section 999 ke under kya punishment hai?"
python3 agent.py "मुझे ऑनलाइन फ्रॉड हुआ, क्या करूँ?"
python3 eval_run.py            # 18-question eval + results/eval_report.md
python3 -m unittest discover -s tests -v   # 17 tests
streamlit run app.py           # trace UI (needs streamlit; .venv provided)
python3 report.py              # eval report from results/results.jsonl
```

## Demo (90 seconds, for judges)

See `demo/demo_script.md` (word for word). In short:

1. **Trap first:** "BNS Section 999 ke under kya punishment hai?" → refuses,
   shows the trap note. "Most agents would hallucinate. Ours shows its work."
2. **Real question, Hinglish:** "Makaan malik bina notice ke nikaal sakta hai
   kya?" → plan → Transfer of Property Act Section 106 (15 days' notice) →
   verified answer in Hinglish, with citations.
3. **Hindi:** "मुझे ऑनलाइन फ्रॉड हुआ, क्या करूँ?" → IT Act 66C / 66D + BNS 318,
   answer in Hindi first (Hindi summary, English chunk cited as source).
   Then cheque bounce → NI Act Section 138.
4. **Scores:** evaluator scores on the 18-question eval set — all 1.0,
   including the 3 traps.
5. **Close:** "Built on my own LawSathi + AgentProof. Planner, retriever,
   verifier, evaluator — one loop, no blind answers."

## Business case (proposed, not launched)

Small law firms / CA-CS firms / legal-aid clinics — **₹999/month per firm**
for verified legal answers with citations, in Hindi and English, on a basic
phone browser.

## Repo layout

| File | What it is |
|---|---|
| `agent.py` | The loop: plan → retrieve → draft → verify → evaluate → answer/refuse |
| `planner.py` | Topic + sub-question decomposition (17 topics, EN + Devanagari keywords) |
| `retriever.py` | Pure-Python BM25 over `data/corpus.jsonl` (71 chunks) |
| `verifier.py` | Sentence-level grounding; unsupported claims dropped |
| `evaluator.py` | AgentProof-style scores (deterministic = hard gate) |
| `checker.py` | Hard gate: no citation may name a section absent from the corpus |
| `config.py` | Thresholds: grounding 0.6, evidence floor 8.0, max 3 loops, top-k 4 |
| `tools.py` | `search_corpus`, `get_section`, `get_case_summary` |
| `eval_run.py` | Reproducible eval runner (benchmark → results + report) |
| `app.py` | Streamlit trace UI, mobile-first (single column, 56px tap targets) |
| `report.py` | Eval report / model card from `results/results.jsonl` |
| `data/corpus.jsonl` | 71 curated chunks, each with act, section, `hi_summary`, source URL |
| `data/benchmark.jsonl` | 18-question eval set (incl. 3 traps) |
| `demo/demo_script.md` | The 90-second pitch, word for word |

## Honest limits

- Corpus is 71 chunks — it covers the most common questions, but the agent
  **refuses** real questions outside it. That is correct behaviour; a bigger
  corpus is the next step, not invented answers.
- The offline drafter quotes chunk text (in English) inside Hinglish answers;
  Hindi answers lead with the chunk's Hindi summary, with the English chunk
  as the cited source. A plugged-in LLM would translate, with the verifier
  still gating.
- BNS/BNSS replaced IPC/CrPC on 1 July 2024 — the corpus labels this
  explicitly and never mixes old and new section numbers silently.
- Legal information, not legal advice. Verify with a lawyer for your case.

## ML.ai usage

See `MLAI.md` and `docs/ML_AI_USAGE.md`. Session evidence goes in
`ml-ai-sessions/` — Sid runs ML.ai in VS Code/Cursor on ≥2 modules before
14 Nov and exports the sessions there. Do not invent session logs.
