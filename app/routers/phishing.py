from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, Response
from supabase import create_client
import os
import uuid
import sendgrid
from sendgrid.helpers.mail import Mail
import hashlib
from fastapi import Request

router = APIRouter(prefix="/phishing", tags=["Phishing"])

# ===============================
# ENV
# ===============================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# TEMP: using Render domain (we will change later)
TRACKING_DOMAIN = "https://cysec-backend.onrender.com"

LANDING_BASE = "https://cysec-phishing-pages.pages.dev"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

# ===============================
# TEST EMAIL
# ===============================

@router.get("/test-email")
def test_email():
    message = Mail(
        from_email="support@cysecguardians.in",
        to_emails="support@cysecguardians.in",
        subject="CySec Test Email",
        html_content="<p>SendGrid is working 🚀</p>"
    )

    try:
        sg.send(message)
        return {"status": "sent"}
    except Exception as e:
        return {"error": str(e)}


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
# TRACK OPEN (FIXED)
# ===============================

@router.get("/track/open")
def track_open(rid: str):

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

    # 1x1 transparent pixel
    pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'

    return Response(content=pixel, media_type="image/gif")


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
    url=f"{LANDING_BASE}/password-reset.html?rid={rid}"
)

# ===============================
# CAPTURE CREDENTIALS
# ===============================

@router.post("/submit")
async def capture_credentials(request: Request):

    data = await request.json()

    rid = data.get("rid")
    email = data.get("email")
    password = data.get("password")

    rec = supabase.table("phishing_recipients") \
        .select("id,campaign_id,email") \
        .eq("unique_id", rid) \
        .execute()

    if not rec.data:
        return {"status": "invalid"}

    recipient = rec.data[0]

    # hash password (never store raw)
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    # store credential
    supabase.table("phishing_credentials").insert({
        "recipient_id": recipient["id"],
        "email_entered": email,
        "password_hash": password_hash
    }).execute()

    # log event
    supabase.table("phishing_events").insert({
        "campaign_id": recipient["campaign_id"],
        "recipient_email": recipient["email"],
        "event_type": "submit"
    }).execute()

    return {"status": "captured"}
