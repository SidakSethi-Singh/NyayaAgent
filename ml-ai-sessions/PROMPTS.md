# PROMPTS.md — ML.ai sessions (NyayaAgent)

Status: **NOT YET RUN** — prepared 2026-11-11 as a fill-in template. No session
below is claimed as done. Fill in each row only after running ML.ai yourself
and exporting the session report into this folder.

## Suggested sessions (from `MLAI.md` — at least 2 modules before 14 Nov 2026)

### Session 1 — Retriever / corpus (suggested)
- **Date:** —
- **Prompt (copy-paste):** "Add 10 more corpus chunks from the BNS/BNSS transition, with sources"
- **Rules:** every new chunk needs a source URL in `data/SOURCES.md`. Do not
  invent section numbers or citations. Every chunk must pass `tests/test_agent.py`.
- **What changed:** —
- **Verification:** `python3 -m unittest discover -s tests` → — / 10 passed
- **Exported session file:** — (save as e.g. `2026-11-12-retriever-session.md`)

### Session 2 — Agent loop (suggested)
- **Date:** —
- **Prompt (copy-paste):** "Wire the LangGraph loop in place of the pure-Python loop in agent.py"
- **Rules:** do not weaken the verifier or the checker to make a demo question
  "pass". No API key, no network call, no aimlapi.com code.
- **What changed:** —
- **Verification:** `python3 -m unittest discover -s tests` → — / 10 passed
- **Exported session file:** — (save as e.g. `2026-11-12-agent-loop-session.md`)

## How to run each session (click-by-click)
1. Open VS Code / Cursor → Open Folder → `workspace/hackathon/NyayaAgent/`.
2. Open the ML.ai extension (ml.ai coding agent — not an API key).
3. Paste one prompt above, let ML.ai propose the change.
4. Review every diff yourself before accepting — especially any new corpus
   chunk or citation.
5. Run `python3 -m unittest discover -s tests` in the terminal. All 10 must pass
   (re-verified 2026-11-11: 10/10 passed before any ML.ai change).
6. Export the ML.ai session report and save it in this folder.
7. Fill in the row above, then add the same date/prompt/change/result to the
   table in `docs/ML_AI_USAGE.md`.

## What NOT to put here
- Do not invent session IDs, screenshots, or logs.
- Do not paste API keys or secrets.
- Do not put aimlapi.com / AI/ML API material here — that is a different service.
