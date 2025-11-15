import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build



def printx():
    print("manash")
    
def create_credentials_from_env(scopes):
    credentials_json = {
        "installed": {
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "project_id": os.environ.get("GOOGLE_PROJECT_ID", "local-project"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "redirect_uris": [os.environ["GOOGLE_REDIRECT_URI"]],
        }
    }

    # Write to memory - not to disk
    flow = InstalledAppFlow.from_client_config(credentials_json, scopes)
    creds = flow.run_local_server(port=0)
    return creds


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_service():
    creds = None

    # Check if token exists
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = create_credentials_from_env(SCOPES)

        # Save new token
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_latest_emails(n=5):
    service = get_service()

    result = service.users().messages().list(
        userId="me",
        maxResults=n,
        labelIds=["INBOX"]
    ).execute()

    messages = result.get("messages", [])
    output = []

    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
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
