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
    import requests
    import json
    import os

    data = {
        "code": code,
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "redirect_uri": os.environ["GOOGLE_REDIRECT_URI"],
        "grant_type": "authorization_code"
    }

    token_res = requests.post("https://oauth2.googleapis.com/token", data=data)
    token_json = token_res.json()

    print("TOKEN RESPONSE:", token_json)

    if "access_token" not in token_json:
        return {"error": token_json}

    with open("token.json", "w") as token:
        token.write(json.dumps(token_json))

    return {"status": "success", "details": "Google account connected!"}


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
