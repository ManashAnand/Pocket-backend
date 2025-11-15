from fastapi import APIRouter
from ..helper.gmail_helper import (
    printx,
    fetch_latest_emails,
    get_service,
    complete_oauth,
    create_auth_url,
)

router = APIRouter()


@router.get('/nice-health')
def nice_health():
    printx()
    return {"health": "nice"}


@router.get("/oauth/callback")
def oauth_callback(code: str):
    """
    Exchange the Google 'code' for access + refresh tokens
    """
    creds = complete_oauth(code)
    
    return {"status": "success"}


@router.get("/emails/latest")
def get_latest_emails(limit: int = 5):
    """
    If no token.json → return OAuth URL
    If token exists → fetch emails
    """
    try:
        service = get_service()

        # First-time login → return URL
        if service == "NEEDS_AUTH":
            return {"auth_url": create_auth_url()}

        # Authenticated → fetch emails
        emails = fetch_latest_emails(limit)
        return {"emails": emails}

    except Exception as e:
        print(e)
        return {"error": str(e)}
