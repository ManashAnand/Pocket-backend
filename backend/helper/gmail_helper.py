import os
import json
from urllib.parse import urlencode

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import requests

SCOPES = "https://www.googleapis.com/auth/gmail.readonly"


def printx():
    print("manash")


# ----------------------------------------------------------
# 1️⃣ CREATE GOOGLE AUTH URL (for mobile / frontend)
# ----------------------------------------------------------
def create_auth_url():
    params = {
        "response_type": "code",
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": os.environ["GOOGLE_REDIRECT_URI"],
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent"
    }

    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


# ----------------------------------------------------------
# 2️⃣ EXCHANGE CODE FOR TOKEN (runs after /oauth/callback)
# ----------------------------------------------------------
def complete_oauth(code: str):
    data = {
        "code": code,
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "redirect_uri": os.environ["GOOGLE_REDIRECT_URI"],
        "grant_type": "authorization_code"
    }

    token_res = requests.post("https://oauth2.googleapis.com/token", data=data)
    token_json = token_res.json()

    if "access_token" not in token_json:
        raise Exception(f"Token error: {token_json}")

    with open("token.json", "w") as f:
        f.write(json.dumps(token_json))

    return token_json


# ----------------------------------------------------------
# 3️⃣ LOAD OR REFRESH TOKEN
# ----------------------------------------------------------
def load_credentials():
    if not os.path.exists("token.json"):
        return None

    with open("token.json", "r") as f:
        saved = json.load(f)

    creds = Credentials(
        token=saved["access_token"],
        refresh_token=saved.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        scopes=[SCOPES]
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open("token.json", "w") as f:
            f.write(creds.to_json())

    return creds


# ----------------------------------------------------------
# 4️⃣ GET SERVICE OR REQUEST AUTH
# ----------------------------------------------------------
def get_service():
    creds = load_credentials()

    # First login → need auth URL
    if creds is None:
        return "NEEDS_AUTH"

    # Create Gmail API client
    return build("gmail", "v1", credentials=creds)


# ----------------------------------------------------------
# 5️⃣ FETCH EMAILS
# ----------------------------------------------------------
def fetch_latest_emails(n=5):
    service = get_service()

    if service == "NEEDS_AUTH":
        return {"auth_url": create_auth_url()}

    results = service.users().messages().list(
        userId="me",
        maxResults=n,
        labelIds=["INBOX"]
    ).execute()

    messages = results.get("messages", [])
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

        output.append({
            "from": data.get("From"),
            "subject": data.get("Subject"),
            "date": data.get("Date"),
            "snippet": msg_data.get("snippet", "")
        })

    return output
