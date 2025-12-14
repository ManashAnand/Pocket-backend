from enum import Enum
from groq import Groq
import os
import json


client = Groq(api_key=os.environ["GROQ_API_KEY"])


class JobVerdict(str, Enum):
    OA_RECEIVED = "oa_received"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
    REFERRED_NO_RESPONSE = "referred_no_response"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    APPLICATION_RECEIVED = "application_received"
    UNKNOWN = "unknown"


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




async def classify_job_emails(emails: list[dict]):
    prompt = f"""
    You are an API. You MUST return valid JSON only.

    Return a JSON array.
    Each element must have exactly these keys:
    - company_name (string)
    - date (string)
    - verdict (string)

    Allowed verdict values:
    oa_received, rejected, ghosted, referred_no_response,
    interview_scheduled, application_received, unknown

    Rules:
    - If the email is NOT related to a job application, still return:
    verdict = "unknown"
    - NEVER return text outside JSON
    - NEVER return markdown
    - NEVER explain anything

    Emails:
    {json.dumps(emails)}
    """

    response = client.chat.completions.create(
        
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=2000,
    )
    raw = response.choices[0].message.content

    print("====== RAW GROQ RESPONSE START ======")
    print(raw)
    print("====== RAW GROQ RESPONSE END ======")

    try:
        return json.loads(raw)
    except Exception as e:
        print("[AI ERROR] JSON parse failed. Falling back.")
        return [
            {
                "company_name": e.get("from", "Unknown"),
                "date": e.get("date", ""),
                "verdict": "unknown"
            }
            for e in emails
        ]


