import os
import json
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Directory for storing per-user tokens
TOKEN_DIR = os.path.join(os.path.dirname(__file__), "..", "tokens")
TOKEN_DIR = os.path.abspath(TOKEN_DIR)

# Ensure it exists
os.makedirs(TOKEN_DIR, exist_ok=True)


def safe_email(email: str) -> str:
    """Convert email into safe filename."""
    return email.replace("@", "_").replace(".", "_")


def token_path_for(email: str) -> str:
    """Generate token file path."""
    return os.path.join(TOKEN_DIR, f"token_{safe_email(email)}.json")


def enforce_token_limit(max_tokens=3):
    """Keep max 3 tokens; delete others."""
    files = sorted(
        [os.path.join(TOKEN_DIR, f) for f in os.listdir(TOKEN_DIR)],
        key=os.path.getmtime,
    )
    if len(files) > max_tokens:
        for f in files[:-max_tokens]:  # delete oldest
            os.remove(f)


def create_auth_url(user_email: str) -> str:
    """Generate Google OAuth URL for this user."""
    params = {
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": os.environ["GOOGLE_REDIRECT_URI"],
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/gmail.readonly",
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": user_email,  # pass email safely
    }

    from urllib.parse import urlencode
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


def complete_oauth(code: str, user_email: str):
    """Exchange code for token & save user's token file."""
    data = {
        "code": code,
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "redirect_uri": os.environ["GOOGLE_REDIRECT_URI"],
        "grant_type": "authorization_code",
    }

    token_res = requests.post("https://oauth2.googleapis.com/token", data=data)
    token_json = token_res.json()

    if "access_token" not in token_json:
        raise Exception(f"Token error: {token_json}")

    enforce_token_limit()
    path = token_path_for(user_email)

    with open(path, "w") as f:
        f.write(json.dumps(token_json))

    print(f"Saved token at: {path}")
    return token_json


def get_service(user_email: str):
    """Load Gmail API service for a specific user's token."""
    path = token_path_for(user_email)

    if not os.path.exists(path):
        # No token → must return OAuth URL
        return {"auth_url": create_auth_url(user_email)}

    token_json = json.load(open(path))

    creds = Credentials(
        token=token_json["access_token"],
        refresh_token=token_json.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=SCOPES,
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(path, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_latest_emails(n: int, service):
    """Fetch latest n emails."""
    result = service.users().messages().list(
        userId="me",
        maxResults=n,
        labelIds=["INBOX"],
    ).execute()

    messages = result.get("messages", [])
    output = []

    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()

        headers = msg_data["payload"]["headers"]
        data = {h["name"]: h["value"] for h in headers}

        output.append(
            {
                "from": data.get("From"),
                "subject": data.get("Subject"),
                "date": data.get("Date"),
                "snippet": msg_data.get("snippet", ""),
            }
        )

    return output
