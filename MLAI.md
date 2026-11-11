# MLAI.md — How ML.ai (the coding agent) is used on NyayaAgent

ML.ai (https://ml.ai) is an **AI coding agent** — VS Code / Cursor extension,
desktop app, terminal, GitHub PR Reviewer. It plans, edits, debugs and tests
code. It is **not** an API key and **not** aimlapi.com. No ML.ai call happens
at runtime: the agent runs offline on the local corpus.

## Workflow (what judges should see)

1. Sid opens this repo in VS Code / Cursor with the ML.ai extension.
2. He prompts ML.ai on at least 2 modules, e.g.:
   - "Add 10 more corpus chunks from the BNS/BNSS transition, with sources"
   - "Wire the LangGraph loop in place of the pure-Python loop in agent.py"
3. He reviews each diff, runs `python3 -m unittest discover -s tests`,
   and exports the session report into `ml-ai-sessions/`.
4. `docs/ML_AI_USAGE.md` records what was prompted, what changed, and the
   test result — with dates. No invented sessions.

## What ML.ai must NOT do here

- Invent corpus chunks, section numbers, or citations. Every chunk needs a
  source URL in `data/SOURCES.md` and must pass `tests/test_agent.py`.
- Weaken the verifier or the checker to make a demo question "pass".
- Add an API key, a network call, or aimlapi.com code.
