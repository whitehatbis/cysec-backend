from fastapi import APIRouter, HTTPException, Query
import os
import requests
from supabase import create_client

router = APIRouter(prefix="/phishing", tags=["Phishing"])

# ===============================
# ENV
# ===============================

GOPHISH_API_KEY = os.getenv("GOPHISH_API_KEY")
GOPHISH_API_URL = os.getenv("GOPHISH_API_URL")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

if not GOPHISH_API_KEY or not GOPHISH_API_URL:
    raise Exception("GoPhish API environment variables missing!")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

HEADERS = {
    "Authorization": f"Bearer {GOPHISH_API_KEY}",
    "Content-Type": "application/json"
}

# ===============================
# TEMPLATE MAP
# ===============================

TEMPLATE_MAP = {
    "invoice_template": 1,
    "login_template": 2,
    "hr_template": 3,
    "high_risk_template": 2,
    "medium_risk_template": 1,
    "basic_template": 1
}

# ===============================
# HELPER
# ===============================

def gophish_request(method, endpoint, data=None):

    url = f"{GOPHISH_API_URL}/api/{endpoint}"

    try:
        if method == "GET":
            r = requests.get(url, headers=HEADERS, verify=False)

        elif method == "POST":
            r = requests.post(url, headers=HEADERS, json=data, verify=False)

        else:
            raise HTTPException(400, "Unsupported method")

        if r.status_code >= 400:
            raise HTTPException(r.status_code, r.text)

        return r.json()

    except requests.exceptions.RequestException as e:
        raise HTTPException(500, str(e))

# ===============================
# CREATE GROUP
# ===============================

@router.post("/group")
def create_group(name: str, emails: list):

    data = {
        "name": name,
        "targets": [{"email": e} for e in emails]
    }

    return gophish_request("POST", "groups/", data)

# ===============================
# LAUNCH CAMPAIGN
# ===============================

@router.post("/campaign")
def launch_campaign(payload: dict):

    template_key = payload.get("template")
    template_id = TEMPLATE_MAP.get(template_key)

    if not template_id:
        raise HTTPException(400, "Unknown template")

    org_id = payload.get("org_id")
    created_by = payload.get("created_by")

    if not org_id:
        raise HTTPException(400, "Missing org_id")

    # MVP static config
    page_id = 1
    smtp_id = 1
    group_id = 1

    data = {
        "name": f"CySec Campaign - {payload.get('goal','test')}",
        "template": {"id": template_id},
        "page": {"id": page_id},
        "smtp": {"id": smtp_id},
        "groups": [{"id": group_id}],
        "launch_date": None,
        "url": payload.get("url", "")
    }

    # 🔥 Create campaign in GoPhish
    result = gophish_request("POST", "campaigns/", data)

    campaign_id = result.get("id")

    # 🔥 Save in Supabase
    supabase.table("phishing_campaigns").insert({
        "org_id": org_id,
        "created_by": created_by,
        "gophish_campaign_id": campaign_id,
        "name": result.get("name"),
        "status": result.get("status"),
        "scheduled_at": result.get("launch_date")
    }).execute()

    # 🔥 AUTO SYNC immediately
    try:
        sync_campaign(campaign_id)
    except Exception as e:
        print("Initial sync failed:", str(e))

    return result

# ===============================
# GET CAMPAIGNS
# ===============================

@router.get("/campaigns")
def get_campaigns(org_id: str = Query(...)):

    campaigns = supabase.table("phishing_campaigns") \
        .select("*") \
        .eq("org_id", org_id) \
        .execute()

    return campaigns.data

# ===============================
# SYNC CAMPAIGN EVENTS
# ===============================

@router.post("/sync/{campaign_id}")
def sync_campaign(campaign_id: int):

    result = gophish_request("GET", f"campaigns/{campaign_id}")
    events = result.get("results", [])

    for e in events:

        email = e.get("email")
        occurred_at = e.get("last_event")

        # 🔥 Prevent duplicates
        existing = supabase.table("phishing_events") \
            .select("id") \
            .eq("campaign_id", campaign_id) \
            .eq("target_email", email) \
            .eq("occurred_at", occurred_at) \
            .execute()

        if existing.data:
            continue

        # 🔥 Map email → employee_id
        employee = supabase.table("employees") \
            .select("id") \
            .eq("email", email) \
            .execute()

        employee_id = employee.data[0]["id"] if employee.data else None

        supabase.table("phishing_events").insert({
            "campaign_id": campaign_id,
            "employee_id": employee_id,
            "target_email": email,
            "gophish_event_type": e.get("status"),
            "occurred_at": occurred_at
        }).execute()

    return {"status": "synced"}

# ===============================
# GET CAMPAIGN RESULTS
# ===============================

@router.get("/campaign/{campaign_id}/results")
def get_campaign_results(campaign_id: int):
    return gophish_request("GET", f"campaigns/{campaign_id}")

# ===============================
# AUTO SYNC ALL CAMPAIGNS
# ===============================

@router.get("/auto-sync")
def auto_sync():

    campaigns = supabase.table("phishing_campaigns") \
        .select("gophish_campaign_id") \
        .execute()

    if not campaigns.data:
        return {"status": "no campaigns"}

    synced = 0

    for c in campaigns.data:
        campaign_id = c.get("gophish_campaign_id")

        if not campaign_id:
            continue

        try:
            sync_campaign(campaign_id)
            synced += 1
        except Exception as e:
            print(f"Failed sync for {campaign_id}: {str(e)}")

    return {
        "status": "success",
        "synced_campaigns": synced
    }
