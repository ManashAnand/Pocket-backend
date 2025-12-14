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
    
    You are validating job application status emails.

Your job is NOT to find job-related content.
Your job is ONLY to identify emails that CONFIRM
an application action the user has ALREADY taken.

━━━━━━━━━━━━━━━━━━━━━━
STRICT DEFINITION
━━━━━━━━━━━━━━━━━━━━━━

An email is a REAL job application update ONLY IF it explicitly confirms
at least ONE of the following actions already happened:

✔ User applied
✔ User was referred
✔ Application was received
✔ Assessment / coding test assigned
✔ Interview scheduled
✔ Rejection sent
✔ Offer made

━━━━━━━━━━━━━━━━━━━━━━
MANDATORY CONFIRMATION SIGNALS
━━━━━━━━━━━━━━━━━━━━━━

At least ONE of these phrases or equivalents must be clearly implied:

- "Thank you for applying"
- "We have received your application"
- "Your application has been submitted"
- "You have been referred"
- "Interview scheduled"
- "Assessment / online test"
- "Shortlisted"
- "We regret to inform you"
- "Offer letter"

━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTELY NOT REAL JOB UPDATES
━━━━━━━━━━━━━━━━━━━━━━

If the email is ANY of the following, it is NOT a real job update:

✖ Job alerts or recommendations  
✖ "You may be a good fit"  
✖ "Apply now"  
✖ Recruiter outreach before applying  
✖ LinkedIn / Indeed / Naukri suggestions  
✖ Reddit, Hirist, newsletters, marketing  
✖ Hiring ads or promotional job emails  

If there is NO explicit confirmation that the user ALREADY applied
or progressed in the hiring process → it is NOT real.

━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (JSON ONLY)
━━━━━━━━━━━━━━━━━━━━━━

Return ONLY a JSON array.
No markdown. No explanation. No extra text.

Each object MUST be exactly:

{
  "company_name": string,
  "date": string,
  "is_real_job_update": boolean,
  "verdict": one of [
    "application_received",
    "referred",
    "oa_received",
    "interview_scheduled",
    "rejected",
    "offer_received",
    "unknown"
  ]
}

━━━━━━━━━━━━━━━━━━━━━━
CRITICAL RULES
━━━━━━━━━━━━━━━━━━━━━━

- Be extremely strict
- If unsure → is_real_job_update = false
- Do NOT guess
- Do NOT infer intent
- Do NOT promote job listings to applications

━━━━━━━━━━━━━━━━━━━━━━
EMAILS TO ANALYZE
━━━━━━━━━━━━━━━━━━━━━━

{{EMAILS_JSON}}

"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a JSON API. "
                    "You must output ONLY valid JSON. "
                    "No explanations. No code. No markdown."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=800,
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
