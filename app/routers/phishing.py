from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from supabase import create_client
import os
import uuid
import sendgrid
from sendgrid.helpers.mail import Mail

router = APIRouter(prefix="/phishing", tags=["Phishing"])

# ===============================
# ENV
# ===============================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

TRACKING_DOMAIN = "https://track.cysecguardians.in"
LANDING_BASE = "https://pages.cysecguardians.in"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

# ===============================
# CREATE CAMPAIGN
# ===============================

@router.post("/campaign")
def create_campaign(payload: dict):
    data = {
        "name": payload.get("name"),
        "template_id": payload.get("template_id"),
        "group_id": payload.get("group_id"),
        "status": "draft"
    }

    res = supabase.table("phishing_campaigns").insert(data).execute()
    return res.data


# ===============================
# ADD RECIPIENTS
# ===============================

@router.post("/campaign/{campaign_id}/recipients")
def add_recipients(campaign_id: str, payload: dict):
    recipients = payload.get("recipients", [])

    records = []
    for r in recipients:
        unique_id = str(uuid.uuid4())

        records.append({
            "campaign_id": campaign_id,
            "email": r["email"],
            "name": r.get("name"),
            "unique_id": unique_id
        })

    supabase.table("phishing_recipients").insert(records).execute()
    return {"status": "added", "count": len(records)}


# ===============================
# SEND CAMPAIGN
# ===============================

@router.post("/campaign/{campaign_id}/send")
def send_campaign(campaign_id: str):

    recipients = supabase.table("phishing_recipients") \
        .select("*") \
        .eq("campaign_id", campaign_id) \
        .execute().data

    if not recipients:
        raise HTTPException(400, "No recipients")

    for r in recipients:

        rid = r["unique_id"]

        tracking_link = f"{TRACKING_DOMAIN}/phishing/track/click?rid={rid}"
        open_pixel = f"{TRACKING_DOMAIN}/phishing/track/open?rid={rid}"

        html = f"""
        <p>Hello {r.get('name','User')},</p>

        <p>We detected an issue that needs your attention.</p>

        <a href="{tracking_link}">Review Now</a>

        <img src="{open_pixel}" width="1" height="1" />

        <hr/>
        <p style="font-size:12px;color:#888;">
        This email is part of a cybersecurity awareness simulation.
        </p>
        """

        message = Mail(
            from_email="support@cysecguardians.in",
            to_emails=r["email"],
            subject="Action Required",
            html_content=html
        )

        message.headers = {
            "X-Cysec-Simulation": "true",
            "X-Campaign-ID": campaign_id,
            "X-Recipient-ID": rid
        }

        try:
            sg.send(message)

            supabase.table("phishing_events").insert({
                "campaign_id": campaign_id,
                "recipient_email": r["email"],
                "event_type": "sent"
            }).execute()

        except Exception as e:
            print("Send failed:", str(e))

    return {"status": "sent"}


# ===============================
# TRACK OPEN
# ===============================

@router.get("/track/open")
def track_open(rid: str):

    # find recipient
    rec = supabase.table("phishing_recipients") \
        .select("campaign_id,email") \
        .eq("unique_id", rid) \
        .execute()

    if rec.data:
        supabase.table("phishing_events").insert({
            "campaign_id": rec.data[0]["campaign_id"],
            "recipient_email": rec.data[0]["email"],
            "event_type": "open"
        }).execute()

    # return 1x1 pixel response
    return {"status": "ok"}


# ===============================
# TRACK CLICK
# ===============================

@router.get("/track/click")
def track_click(rid: str):

    rec = supabase.table("phishing_recipients") \
        .select("campaign_id,email") \
        .eq("unique_id", rid) \
        .execute()

    if rec.data:
        supabase.table("phishing_events").insert({
            "campaign_id": rec.data[0]["campaign_id"],
            "recipient_email": rec.data[0]["email"],
            "event_type": "click"
        }).execute()

    return RedirectResponse(
        url=f"{LANDING_BASE}/password-reset?rid={rid}"
    )
