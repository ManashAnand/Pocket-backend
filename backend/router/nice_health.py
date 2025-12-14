from fastapi import APIRouter, Request
from ..helper.gmail_helper import (
    get_service,
    fetch_latest_emails,
    complete_oauth,
)
from ..helper.ai import normalize_emails,classify_job_emails,chunk_list
import asyncio
from fastapi import BackgroundTasks


router = APIRouter()

job_status = {}
job_results = {}


@router.get("/nice-health")
def nice_health():
    return {"health": "nice"}

BATCH_SIZE = 5 

async def run_classification_pipeline(user_email: str, limit: int):
    try:
        job_status[user_email] = "processing"

        service = get_service(user_email)
        emails = fetch_latest_emails(limit, service)
        normalized = normalize_emails(emails)

        all_results = []

        for batch in chunk_list(normalized, BATCH_SIZE):
            batch_result = await classify_job_emails(batch)
            all_results.extend(batch_result)
            await asyncio.sleep(0.4)

        job_results[user_email] = all_results
        job_status[user_email] = "done"

    except Exception as e:
        job_status[user_email] = "error"
        job_results[user_email] = {"error": str(e)}

@router.get("/emails/latest")
async def get_latest_emails(
    user_email: str,
    limit: int = 50,
    background_tasks: BackgroundTasks = None,
):
    service = get_service(user_email)

    if isinstance(service, dict) and "auth_url" in service:
        return {"auth_url": service["auth_url"]}

    if job_status.get(user_email) == "processing":
        return {"status": "processing"}

    background_tasks.add_task(run_classification_pipeline, user_email, limit)
    job_status[user_email] = "processing"

    return {"status": "started"}

@router.get("/emails/status")
async def get_email_status(user_email: str):
    status = job_status.get(user_email, "not_started")

    if status == "done":
        return {
            "status": "done",
            "job_emails": job_results.get(user_email, [])
        }

    if status == "error":
        return {
            "status": "error",
            "detail": job_results.get(user_email)
        }

    return {"status": status}


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
