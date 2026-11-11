# NyayaAgent — 90-second demo script (INFRASHIFT, 14 Nov 2026)

**Setup:** `streamlit run app.py` on a phone browser. The first screen shows
four big buttons — tap the trap first. Have `results/eval_report.md` open
in a second tab. All numbers below are measured (`python3 eval_run.py`):
18 questions, 18/18 gates passed, 3 traps refused.

## 0:00–0:20 — The trap (the hook)
> "Most legal chatbots will answer anything — even a law that doesn't exist.
> Watch this: *BNS Section 999 ke under kya punishment hai?*"
> → Tap the first button. Agent **refuses**: "Is sawal ke liye hamare corpus
> mein kaafi verified saboot nahi hai." Show the trace: cited section 999 is
> in no chunk, and the checker is the hard gate. "Most agents would
> hallucinate. Ours shows its work."

## 0:20–0:45 — The real question, in Hinglish
> "Ab asli sawal — *Makaan malik bina notice ke nikaal sakta hai kya?*"
> → Tap the second button. Plan appears (tenancy → notice, section, force,
> lease end) → retrieves Transfer of Property Act **Section 106** → answer in
> Hinglish: 15 days' notice for a monthly tenancy, no forceful eviction.
> Click the citation — the exact chunk opens, with its India Code source.

## 0:45–1:05 — Hindi + a second trap
> "मुझे ऑनलाइन फ्रॉड हुआ, क्या करूँ?" → IT Act 66C / 66D + BNS 318, answer
> in Hindi first (Hindi summary, English chunk cited as source).
> Then, if time: "Cheque bounce ho gaya?" → NI Act Section 138.
> Show the evaluator scores: groundedness 1.0, citation coverage 1.0,
> refusal correctness 1.0, language match 1.0 — on all 18 eval questions,
> including 3 traps. "Every claim is checked against the text it quotes.
> Unsupported sentences are dropped, not polished. A weak match is refused
> too — 'own land on the Moon' gets no answer."

## 1:05–1:30 — Close with the business case
> "Built on my own LawSathi + AgentProof. Planner, retriever, verifier,
> evaluator — one loop, no blind answers. 71 verified chunks across 22 Acts.
> For small law firms and legal-aid clinics: ₹999 a month per firm, verified
> answers in Hindi and English, on a basic phone. Legal information, not
> legal advice."

## If a judge asks
- **"ML.ai kaise use kiya?"** → `MLAI.md` + `ml-ai-sessions/` (Sid's real
  exported sessions; nothing invented).
- **"Why did it refuse my question?"** → open the trace: either the section
  is in no chunk, the case is not in the corpus, or the best retrieval score
  was below the evidence floor (8.0). Refusal is the feature.
- **"Is the corpus big enough?"** → honest answer: 71 chunks covers the most
  common questions; anything outside it is refused rather than guessed.
  Growing the corpus is the next step, not inventing answers.
