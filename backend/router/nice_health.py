from fastapi import APIRouter, Request
from ..helper.gmail_helper import (
    get_service,
    fetch_latest_emails,
    complete_oauth,
)
from ..helper.ai import normalize_emails,classify_job_emails

router = APIRouter()


@router.get("/nice-health")
def nice_health():
    return {"health": "nice"}


@router.get("/emails/latest")
async def get_latest_emails(user_email: str, limit: int = 5):
    """Check if token exists → fetch emails OR return OAuth URL."""
    service = get_service(user_email)

    if isinstance(service, dict) and "auth_url" in service:
        return {"auth_url": service["auth_url"]}

    emails = fetch_latest_emails(limit, service)
    print(f"Emails from nice_health {emails}")
    normalized = normalize_emails(emails)
    print(f"normalized Emails from nice_health {normalized}")

    job_results = await classify_job_emails(normalized)
    print(f"job_results  from nice_health {job_results}")
    return {
        "count": len(job_results),
        "job_emails": job_results
    }

@router.get("/oauth/callback")
def oauth_callback(code: str, state: str):
    """
    Google redirects with:
    - code = authorization code
    - state = user_email (we passed earlier)
    """
    user_email = state  # state contains email

    try:
        complete_oauth(code, user_email)
        return {"status": "success", "message": "Google account linked!"}
    except Exception as e:
        return {"error": str(e)}
