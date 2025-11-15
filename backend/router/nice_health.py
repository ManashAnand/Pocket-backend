from fastapi import APIRouter
from ..helper import printx,fetch_latest_emails

router = APIRouter()

@router.get('/nice-health')
def nice_health():
    printx()
    return {"health":"nice"}



@router.get("/emails/latest")
def get_latest_emails(limit: int = 5):
    emails = fetch_latest_emails(limit)
    return {"emails": emails}