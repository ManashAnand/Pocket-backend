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

def normalize_emails(emails):
    normalized = []
    for e in emails:
        normalized.append({
            "id": e.get("id"),
            "subject": e.get("subject", ""),
            "from": e.get("from", ""),
            "date": e.get("date", ""),
            "body": e.get("snippet", "")[:1500]  # trim hard
        })
    return normalized



async def classify_job_emails(emails: list[dict]):
    prompt = f"""
You are an email classifier for job applications.

For each email, extract:
1. company_name
2. date (from email body, NOT today's date)
3. verdict

Allowed verdict values:
- oa_received
- rejected
- ghosted
- referred_no_response
- interview_scheduled
- application_received
- unknown

Rules:
- OA link or assessment → oa_received
- Rejection wording → rejected
- Referral mention without reply → referred_no_response
- Interview mention → interview_scheduled
- Confirmation only → application_received
- Unclear → unknown

Return ONLY valid JSON array.

Emails:
{json.dumps(emails)}
"""

    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content
    return json.loads(raw)
