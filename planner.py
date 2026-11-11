"""Planner — decomposes a question into 2-4 sub-questions.

Rule-based and deterministic (no LLM needed): it matches the question to
known legal topics, then emits sub-questions for the applicable law, the
relevant section, the exceptions, and the procedure. Unknown topics fall
back to a generic plan so the retriever still gets a fair shot.
"""
import re

TOPICS = {
    "tenancy": {
        "keywords": ["landlord", "tenant", "rent", "evict", "eviction", "makaan",
                     "malik", "kiraya", "kirayedar", "nikaal", "ghar", "notice to quit", "मकान", "मालिक", "किराया", "किरायेदार", "निकाल", "नोटिस", "घर"],
        "sub_questions": [
            "What notice must a landlord give before ending a tenancy?",
            "Which section governs notice to quit for a monthly tenancy?",
            "Can a landlord evict a tenant by force without a court process?",
            "How does a lease legally come to an end?",
        ],
    },
    "consumer": {
        "keywords": ["consumer", "refund", "defective", "product", "service", "shop",
                     "seller", "complaint", "upbhokta", "kharab", "paise wapas", "उपभोक्ता", "शिकायत", "खराब", "पैसे वापस", "दोष"],
        "sub_questions": [
            "Who counts as a consumer under the law?",
            "What is an unfair trade practice?",
            "Where should a consumer complaint be filed, and up to what value?",
        ],
    },
    "cyber": {
        "keywords": ["online", "fraud", "otp", "upi", "phishing", "hacked", "identity",
                     "cheat", "scam", "dhokha", "fraud", "password", "account", "ऑनलाइन", "फ्रॉड", "धोखा", "ठगी", "हैक", "ओटीपी", "पासवर्ड"],
        "sub_questions": [
            "What law covers identity theft online?",
            "What is the punishment for cheating by personation using a computer?",
            "Which section covers cheating in general, and what is its punishment?",
        ],
    },
    "contract": {
        "keywords": ["contract", "agreement", "breach", "damages", "samjhauta", "theka", "समझौता", "ठेका", "अनुबंध"],
        "sub_questions": [
            "What makes an agreement a valid contract?",
            "What compensation is available when a contract is broken?",
        ],
    },
    "company": {
        "keywords": ["company", "director", "private limited", "board", "startup", "firm"],
        "sub_questions": [
            "What is a private company?",
            "How many directors must a company have?",
        ],
    },
    "constitutional": {
        "keywords": ["fundamental right", "constitution", "article", "freedom of speech",
                     "equality", "supreme court", "writ", "samvidhan", "adhikar", "संविधान", "अधिकार", "मौलिक"],
        "sub_questions": [
            "What does Article 14 equality before law say?",
            "What does Article 19 freedom of speech and expression say?",
            "What does Article 21 protection of life and personal liberty say?",
            "Can the Supreme Court be approached directly for a fundamental right?",
        ],
    },
    "criminal": {
        "keywords": ["murder", "theft", "cheating", "fir", "police", "arrest", "hatya",
                     "chori", "shikayat", "हत्या", "चोरी", "पुलिस", "शिकायत", "एफआईआर", "गिरफ्तार"],
        "sub_questions": [
            "Which section defines this offence?",
            "What is the punishment for this offence?",
            "How is a First Information Report filed?",
        ],
    },
    "rti": {
        "keywords": ["rti", "information", "government", "sarkari", "suchna", "सूचना", "सरकारी"],
        "sub_questions": [
            "How does a person request information under the RTI Act?",
            "Within how many days must information be provided?",
        ],
    },
    "motor": {
        "keywords": ["accident", "vehicle", "car", "road", "compensation", "durghatna", "gaadi", "दुर्घटना", "गाड़ी", "सड़क", "मुआवजा"],
        "sub_questions": [
            "What compensation is payable for death or grievous hurt in a motor accident?",
            "Must the claimant prove fault to get that compensation?",
        ],
    },
    "family": {
        "keywords": ["divorce", "marriage", "talaq", "shaadi", "cruelty", "desertion", "maintenance", "alimony", "bharana", "poshan", "तलाक", "शादी", "क्रूरता", "भरण", "पोषण", "गुजारा"],
        "sub_questions": [
            "On what grounds can a marriage be dissolved by divorce?",
            "How long must desertion continue before it is a ground for divorce?",
            "Can divorce be granted by mutual consent?",
            "What maintenance can be claimed during and after divorce proceedings?",
        ],
    },
    "cheque": {
        "keywords": ["cheque", "check", "bounce", "dishonour", "dishonor", "ni act", "138", "चेक", "बाउंस"],
        "sub_questions": [
            "What is the offence when a cheque is dishonoured for insufficiency of funds?",
            "What presumption applies in favour of the holder of a cheque?",
            "How and within what time must a cheque-bounce complaint be filed?",
        ],
    },
    "employment": {
        "keywords": ["job", "fired", "terminated", "retrench", "retrenchment", "gratuity", "maternity", "salary", "wages", "minimum wage", "naukri", "nikala", "नौकरी", "निकाल", "वेतन", "मजदूरी", "ग्रेच्युटी"],
        "sub_questions": [
            "What conditions must be met before retrenching a workman?",
            "When is gratuity payable and how is it calculated?",
            "What maternity benefit is a woman employee entitled to?",
            "Must an employer pay at least the minimum rate of wages?",
        ],
    },
    "property": {
        "keywords": ["registration", "sale deed", "property", "registry", "will", "vasiyat", "succession", "inherit", "wasihat", "sampatti", "रजिस्ट्री", "संपत्ति", "वसीयत", "उत्तराधिकार", "विरासत"],
        "sub_questions": [
            "Which property documents must be registered?",
            "What happens if a document that must be registered is not registered?",
            "What is a sale of immovable property and how is it made?",
            "How is a will executed and who inherits without a will?",
        ],
    },
    "bail": {
        "keywords": ["bail", "jamanat", "anticipatory", "जमानत", "अग्रिम"],
        "sub_questions": [
            "When must a person arrested for a bailable offence be released on bail?",
            "Can a court grant bail in a non-bailable offence?",
            "When may police arrest without a warrant?",
        ],
    },
    "defamation": {
        "keywords": ["defamation", "defame", "manhani", "badnami", "मानहानि", "बदनामी"],
        "sub_questions": [
            "What counts as defamation under the law?",
            "What is the punishment for defamation?",
        ],
    },
    "gst": {
        "keywords": ["gst", "tax", "income tax", "return", "input tax credit", "itc", "टैक्स", "आयकर", "रिटर्न"],
        "sub_questions": [
            "Who must file a return of income?",
            "When can a registered person take input tax credit?",
            "What penalty applies for GST offences such as supplying without an invoice?",
        ],
    },
    "criminal_extra": {
        "keywords": ["hurt", "intimidation", "threat", "dhamki", "chot", "धमकी", "चोट", "मारपीट"],
        "sub_questions": [
            "What is voluntarily causing hurt and its punishment?",
            "What is criminal intimidation and its punishment?",
        ],
    },
}


def detect_language(question: str) -> str:
    """'hi' if Devanagari present, 'hinglish' if Roman Hindi words appear, else 'en'."""
    if re.search(r"[\u0900-\u097F]", question):
        return "hi"
    hinglish_words = {"kya", "hai", "nahi", "kaise", "kab", "kyun", "mera", "tumhara",
                      "sakte", "sakta", "chahiye", "bina", "liye", "mein", "se", "ko"}
    words = set(re.findall(r"[a-z]+", question.lower()))
    if words & hinglish_words:
        return "hinglish"
    return "en"


def plan(question: str) -> dict:
    """Return {'topics': [...], 'sub_questions': [...], 'language': ...}."""
    q = question.lower()
    topics = [name for name, t in TOPICS.items()
              if any(k in q for k in t["keywords"])]
    sub_questions = []
    for name in topics:
        sub_questions.extend(TOPICS[name]["sub_questions"])
    if not sub_questions:
        sub_questions = [
            "Which law and section apply to this question?",
            "What does that section actually say?",
            "What procedure or remedy follows from it?",
        ]
    # A fake section number (e.g. BNS 999, IPC 420A) is a trap: plan a check for it.
    if re.search(r"(section|sec\.?|dhara)\s*\d{3,}", q) or re.search(r"\b\d{3,}\b", q):
        sub_questions.append("Does the cited section number actually exist in the corpus?")
    return {"topics": topics or ["general"],
            "sub_questions": sub_questions[:4],
            "language": detect_language(question)}
