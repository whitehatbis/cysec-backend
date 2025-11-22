from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from supabase import create_client
import os
import json
import requests

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

SCOPES = ["https://www.googleapis.com/auth/admin.directory.user.readonly"]

# 1️⃣ Generate Google OAuth URL
@router.get("/google/auth-url")
def google_auth_url():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return {"auth_url": auth_url}

# 2️⃣ Handle OAuth Callback
@router.get("/google/callback")
def google_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    flow.fetch_token(code=code)

    creds = flow.credentials

    # Store refresh token in memory (MVP)
    with open("google_token.json", "w") as f:
        f.write(creds.to_json())

    return {"message": "Google connected successfully"}

# 3️⃣ Sync Users Into Supabase
@router.post("/google/sync-users")
def sync_users(org_id: str):
    if not os.path.exists("google_token.json"):
        raise HTTPException(status_code=401, detail="Google not connected")

    creds = Credentials.from_authorized_user_file("google_token.json", SCOPES)
    service = build("admin", "directory_v1", credentials=creds)

    results = service.users().list(customer="my_customer").execute()
    users = results.get("users", [])

    synced = 0

    for user in users:
        if "primaryEmail" not in user:
            continue

        email = user["primaryEmail"]
        name = user.get("name", {}).get("fullName", "")
        department = user.get("organizations", [{}])[0].get("department", "")

        supabase.table("employees").upsert({
            "org_id": org_id,
            "email": email,
            "name": name,
            "department": department,
            "status": "active"
        }).execute()

        synced += 1

    return {"message": f"Synced {synced} users successfully"}
