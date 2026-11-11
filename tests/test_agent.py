"""Tests for NyayaAgent MVP — run with: python3 -m unittest discover -s tests -v"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent import ask  # noqa: E402
from checker import check_answer  # noqa: E402
from planner import plan  # noqa: E402
from retriever import Corpus, load_retriever  # noqa: E402
from verifier import verify  # noqa: E402

RETRIEVER = load_retriever()


class TestPlanner(unittest.TestCase):
    def test_landlord_question_plans_tenancy(self):
        p = plan("Makaan malik bina notice ke nikaal sakta hai kya?")
        self.assertIn("tenancy", p["topics"])
        self.assertEqual(p["language"], "hinglish")
        self.assertGreaterEqual(len(p["sub_questions"]), 2)

    def test_hindi_detected(self):
        self.assertEqual(plan("मकान मालिक बिना नोटिस के निकाल सकता है क्या?")["language"], "hi")


class TestRetriever(unittest.TestCase):
    def test_landlord_finds_section_106(self):
        top = RETRIEVER.retrieve("landlord evict tenant without notice", k=4)
        self.assertTrue(any("106" in r["chunk"]["section"] for r in top))

    def test_fake_section_scores_zero(self):
        top = RETRIEVER.retrieve("BNS Section 999 punishment", k=4)
        self.assertFalse(any("999" in r["chunk"]["section"] for r in top))

    def test_corpus_has_sources(self):
        for c in RETRIEVER.corpus.chunks:
            self.assertTrue(c["source_url"].startswith("https://"))
            self.assertIn("act", c)
            self.assertIn("section", c)


class TestCorpusV2(unittest.TestCase):
    def test_corpus_has_at_least_60_chunks(self):
        self.assertGreaterEqual(len(RETRIEVER.corpus.chunks), 60)

    def test_every_chunk_has_hindi_summary_and_real_source(self):
        for c in RETRIEVER.corpus.chunks:
            self.assertTrue(c.get("hi_summary"), c["section"])
            self.assertTrue(c["source_url"].startswith("https://www.indiacode.nic.in/"),
                            c["section"])
            self.assertIn("act", c)
            self.assertIn("section", c)

    def test_new_topics_planned(self):
        self.assertIn("cheque", plan("My cheque bounced, what do I do?")["topics"])
        self.assertIn("employment", plan("Company fired me without notice")["topics"])
        self.assertIn("bail", plan("Bailable offence mein bail kaise milti hai?")["topics"])
        self.assertIn("gst", plan("What is the GST penalty?")["topics"])


class TestVerifier(unittest.TestCase):
    def test_unsupported_claim_dropped(self):
        chunks = [c for c in RETRIEVER.corpus.chunks if "106" in c["section"]]
        result = verify(
            ["Under Section 106, a monthly tenancy needs fifteen days notice.",
             "The landlord may also seize the tenant's passport under Section 999."],
            chunks)
        self.assertEqual(len(result["supported"]), 1)
        self.assertEqual(len(result["unsupported"]), 1)
        self.assertEqual(result["groundedness"], 0.5)


class TestAgentEndToEnd(unittest.TestCase):
    def test_hinglish_landlord_answered_with_citation(self):
        r = ask("Makaan malik bina notice ke nikaal sakta hai kya?",
                retriever=RETRIEVER)
        self.assertFalse(r["refused"])
        self.assertIn("106", r["answer"])
        self.assertGreaterEqual(r["scores"]["groundedness"], 0.6)
        self.assertTrue(r["scores"]["passed"])
        self.assertEqual(check_answer(r["answer"], RETRIEVER.corpus, False), [])

    def test_trap_fake_section_refused(self):
        r = ask("BNS Section 999 ke under kya punishment hai?",
                retriever=RETRIEVER)
        self.assertTrue(r["refused"])
        self.assertNotIn("999", r["answer"].split("Evaluator scores:")[0])
        self.assertEqual(r["scores"]["refusal_correctness"], 1.0)

    def test_english_consumer_question(self):
        r = ask("I bought a defective phone, where can I complain?",
                retriever=RETRIEVER)
        self.assertFalse(r["refused"])
        self.assertIn("Consumer Protection Act", r["answer"])

    def test_fundamental_rights_stays_constitutional(self):
        r = ask("What are my fundamental rights?", retriever=RETRIEVER)
        self.assertFalse(r["refused"])
        self.assertIn("Constitution of India", r["answer"])
        self.assertNotIn("Companies Act", r["answer"])
        self.assertGreaterEqual(r["scores"]["groundedness"], 0.6)

    def test_trap_fake_case_refused(self):
        r = ask("In Sharma v. State of Delhi 2024, the Supreme Court held that "
                "data privacy is absolute. Is that correct?", retriever=RETRIEVER)
        self.assertTrue(r["refused"])
        self.assertEqual(r["scores"]["refusal_correctness"], 1.0)

    def test_trap_out_of_corpus_topic_refused(self):
        r = ask("Can I legally own land on the Moon?", retriever=RETRIEVER)
        self.assertTrue(r["refused"])

    def test_hindi_answer_reads_in_hindi(self):
        r = ask("मुझे ऑनलाइन फ्रॉड हुआ, क्या करूँ?", retriever=RETRIEVER)
        self.assertFalse(r["refused"])
        body = r["answer"].split("Evaluator scores:")[0]
        # Devanagari in the answer body itself (not just the disclaimer).
        self.assertRegex(body, r"[\u0900-\u097F]")
        self.assertEqual(r["scores"]["language_match"], 1.0)

    def test_cheque_bounce_answered_with_ni_act_138(self):
        r = ask("My tenant's rent cheque bounced. What can I do under NI Act Section 138?",
                retriever=RETRIEVER)
        self.assertFalse(r["refused"])
        self.assertIn("138", r["answer"])


if __name__ == "__main__":
    unittest.main()
