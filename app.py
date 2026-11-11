"""Streamlit trace UI — mobile-first, single column (INFRASHIFT demo rule).

Run: streamlit run app.py
Shows the full agent trace: plan → retrieved chunks → verification verdicts
→ evaluator scores → final answer, with citations to source text.

Mobile-first on purpose: single column, no sidebar, full-width buttons
with min-height 56px, Hindi + Hinglish prompts visible on the first screen
— the demo must work end to end on a basic phone browser.
"""
import streamlit as st

from agent import ask

st.set_page_config(page_title="NyayaAgent — Verified Legal Answers",
                   page_icon="⚖️", layout="centered",
                   initial_sidebar_state="collapsed")

# Mobile-first CSS: big text, big full-width buttons, no cramped columns.
st.markdown(
    """
    <style>
    html, body, [class*="css"] { font-size: 18px; }
    .stButton > button {
        width: 100%; min-height: 56px; font-size: 18px;
        border-radius: 12px; white-space: normal; text-align: left;
        padding: 12px 16px;
    }
    .stTextInput input { font-size: 18px; min-height: 52px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("⚖️ NyayaAgent")
st.caption("Verified Indian legal answers — plan, retrieve, verify, then answer. "
           "Legal information, not legal advice.")

DEMO_QUESTIONS = [
    ("🚫 Trap first: BNS Section 999?", "BNS Section 999 ke under kya punishment hai?"),
    ("🏠 Hinglish: Makaan malik bina notice ke nikaal sakta hai kya?",
     "Makaan malik bina notice ke nikaal sakta hai kya?"),
    ("🇮🇳 हिंदी: मुझे ऑनलाइन फ्रॉड हुआ, क्या करूँ?",
     "मुझे ऑनलाइन फ्रॉड हुआ, क्या करूँ?"),
    ("💬 Hinglish: Cheque bounce ho gaya, kya karoon?",
     "My tenant's rent cheque bounced. What can I do under NI Act Section 138?"),
]

q = st.text_input("Apna sawal poochho (English / Hindi / Hinglish):",
                  placeholder="Makaan malik bina notice ke nikaal sakta hai kya?")
st.write("Try one — ek sawal chunein:")
for label, dq in DEMO_QUESTIONS:
    if st.button(label, key=f"demo-{dq[:20]}"):
        q = dq

if q and st.button("✨ Ask NyayaAgent", type="primary"):
    with st.spinner("Planning → retrieving → verifying…"):
        r = ask(q, log_path="results/results.jsonl")
    st.subheader("📋 Plan")
    st.write("Topics:", ", ".join(r["plan"]["topics"]))
    for sq in r["plan"]["sub_questions"]:
        st.write("•", sq)
    for loop in r["loops"]:
        with st.expander(f"🔁 Loop {loop['loop']} — groundedness {loop['groundedness']:.2f}"):
            for item in loop["retrieved"]:
                st.write("•", item)
            if loop["unsupported"]:
                st.warning("Dropped as unsupported: " + "; ".join(loop["unsupported"]))
    if r.get("trap"):
        st.warning(f"🪤 Trap check: {r['trap']}")
    st.subheader("📊 Evaluator scores")
    st.json(r["scores"])
    st.subheader("✅ Answer" if not r["refused"] else "🚫 Refused — not enough evidence")
    st.write(r["answer"])
    if r["checker_problems"]:
        st.error("Checker problems: " + "; ".join(r["checker_problems"]))
