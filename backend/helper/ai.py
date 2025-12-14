from enum import Enum
from groq import Groq
import os
import json


client = Groq(api_key=os.environ["GROQ_API_KEY"])

async def get_all_jobs_email(email):
    print(f"all emails regarding jobs are {email}")
    return {"job_email":email}

def smart_snippet(text: str, head=300, tail=200):
    if len(text) <= head + tail:
        return text
    return text[:head] + "\n...\n" + text[-tail:]

def normalize_emails(emails):
    normalized = []
    for e in emails:
        body = e.get("snippet", "")
        normalized.append({
            "subject": e.get("subject", "")[:200],
            "from": e.get("from", "")[:100],
            "date": e.get("date", ""),
            "body": smart_snippet(body),
        })
    return normalized

def chunk_list(items, chunk_size):
    for i in range(0, len(items), chunk_size):
        yield items[i:i + chunk_size]


JOB_KEYWORDS = [
    "job", "application", "applied", "career", "hiring",
    "interview", "assessment", "coding", "test",
    "recruit", "recruiter", "selection", "shortlisted",
    "offer", "position", "role"
]

JOB_SENDERS = [
    "careers", "recruit", "jobs", "talent", "hr", "hiring"
]

ATS_PROVIDERS = [
    "greenhouse", "lever", "workday"
]

def job_score(email: dict) -> int:
    score = 0

    subject = (email.get("subject") or "").lower()
    snippet = (email.get("snippet") or "").lower()
    sender = (email.get("from") or "").lower()

    text = subject + " " + snippet

    # keyword matches
    for kw in JOB_KEYWORDS:
        if kw in text:
            score += 2

    # sender hints
    for s in JOB_SENDERS:
        if s in sender:
            score += 2

    # ATS detection (very strong signal)
    for ats in ATS_PROVIDERS:
        if ats in sender:
            score += 3

    return score


def extract_json_array(text: str) -> list:
    start = text.find("[")
    if start == -1:
        raise ValueError("No JSON array start")

    depth = 0
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])

    raise ValueError("No complete JSON array found")


async def classify_job_emails(emails: list[dict]):
    prompt = f"""
You are classifying emails related to job applications.

Your task:
1. Decide whether the email is a REAL job application update.
2. If yes, classify the status.

A REAL job application update means:
- confirmation that YOU applied
- online assessment / coding test
- interview scheduling
- rejection
- offer

NOT real job updates:
- job listings or promotions
- recruiter outreach before applying
- LinkedIn notifications
- banks, govt, product, newsletters
- hiring ads, portals, marketing

Return ONLY a JSON array.
Each item must be:

{{
  "company_name": string,
  "date": string,
  "is_real_job_update": boolean,
  "verdict": one of [
    "application_received",
    "oa_received",
    "interview_scheduled",
    "rejected",
    "offer_received",
    "unknown"
  ]
}}

Rules:
- If not a real job update, set is_real_job_update = false.
- If unsure, set is_real_job_update = false.
- Be strict. Do not guess.

Emails:
{json.dumps(emails)}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=800,
        stop=["```", "def ", "import ", "Example", "Explanation"],
    )

    raw = response.choices[0].message.content

    print("====== RAW GROQ RESPONSE START ======")
    print(raw)
    print("====== RAW GROQ RESPONSE END ======")

    try:
        results = extract_json_array(raw)

        real_job_emails = [
            {
                "company_name": r.get("company_name", "Unknown"),
                "date": r.get("date", ""),
                "verdict": r.get("verdict", "unknown"),
                "is_real_job_update": True,
            }
            for r in results
            if r.get("is_real_job_update") is True
        ]

        return real_job_emails

    except Exception as e:
        print("[AI ERROR] JSON parse failed:", e)
        return [
            {
                "company_name": e.get("from", "Unknown"),
                "date": e.get("date", ""),
                "verdict": "unknown",
                "is_real_job_update": False,
            }
            for e in emails
        ]
