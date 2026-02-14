from fastapi import APIRouter, HTTPException
import os
import requests

router = APIRouter(prefix="/phishing", tags=["Phishing"])

GOPHISH_API_KEY = os.getenv("GOPHISH_API_KEY")
GOPHISH_API_URL = os.getenv("GOPHISH_API_URL")

if not GOPHISH_API_KEY or not GOPHISH_API_URL:
    raise Exception("GoPhish API environment variables missing!")

HEADERS = {
    "Authorization": f"Bearer {GOPHISH_API_KEY}",
    "Content-Type": "application/json"
}

# ===============================================
# TEMPLATE MAP (YOUR REAL IDs)
# ===============================================

TEMPLATE_MAP = {
    "invoice_template": 1,
    "login_template": 2,
    "hr_template": 3,
    "high_risk_template": 2,
    "medium_risk_template": 1,
    "basic_template": 1
}

# ===============================================
# HELPER
# ===============================================

def gophish_request(method, endpoint, data=None):

    url = f"{GOPHISH_API_URL}/api/{endpoint}"

    try:

        if method == "GET":
            r = requests.get(
                url,
                headers=HEADERS,
                verify=False
            )

        elif method == "POST":
            r = requests.post(
                url,
                headers=HEADERS,
                json=data,
                verify=False
            )

        else:
            raise HTTPException(400, "Unsupported method")

        if r.status_code >= 400:
            raise HTTPException(r.status_code, r.text)

        return r.json()

    except requests.exceptions.RequestException as e:
        raise HTTPException(500, str(e))


# ===============================================
# CREATE GROUP (optional)
# ===============================================

@router.post("/group")
def create_group(name: str, emails: list):

    data = {
        "name": name,
        "targets": [{"email": e} for e in emails]
    }

    return gophish_request("POST", "groups/", data)


# ===============================================
# LAUNCH CAMPAIGN (MAIN ENDPOINT)
# ===============================================

@router.post("/campaign")
def launch_campaign(payload: dict):

    """
    Accepts wizard campaignDraft directly.
    """

    template_key = payload.get("template")
    template_id = TEMPLATE_MAP.get(template_key)

    if not template_id:
        raise HTTPException(400, "Unknown template")

    # MVP hardcoded values
    # (replace later with dynamic values)
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

    return gophish_request("POST", "campaigns/", data)


# ===============================================
# GET CAMPAIGNS
# ===============================================

@router.get("/campaigns")
def get_campaigns():
    return gophish_request("GET", "campaigns/")


# ===============================================
# RESULTS
# ===============================================

@router.get("/campaign/{campaign_id}/results")
def get_campaign_results(campaign_id: int):
    return gophish_request("GET", f"campaigns/{campaign_id}")
