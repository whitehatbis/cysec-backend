from fastapi import APIRouter, HTTPException
import os
import requests

router = APIRouter(prefix="/phishing", tags=["Phishing"])

GOPHISH_API_KEY = os.getenv("GOPHISH_API_KEY")
GOPHISH_API_URL = os.getenv("GOPHISH_API_URL")  # e.g. https://XX.XX.XX.XX:3333

if not GOPHISH_API_KEY or not GOPHISH_API_URL:
    raise Exception("GoPhish API environment variables missing!")


# -----------------------------------------------
# Helper Function: Make requests to GoPhish API
# -----------------------------------------------
def gophish_request(method, endpoint, data=None):
    url = f"{GOPHISH_API_URL}/api/{endpoint}?api_key={GOPHISH_API_KEY}"

    try:
        if method == "GET":
            response = requests.get(url, verify=False)
        elif method == "POST":
            response = requests.post(url, json=data, verify=False)
        else:
            raise HTTPException(400, "Unsupported method")

        if response.status_code >= 400:
            raise HTTPException(response.status_code, response.text)

        return response.json()

    except requests.exceptions.RequestException as e:
        raise HTTPException(500, str(e))


# -----------------------------------------------
# Create Email Template
# -----------------------------------------------
@router.post("/template")
def create_template(name: str, subject: str, html: str):
    data = {
        "name": name,
        "subject": subject,
        "html": html
    }

    return gophish_request("POST", "templates/", data)


# -----------------------------------------------
# Create Target Group
# -----------------------------------------------
@router.post("/group")
def create_group(name: str, emails: list):
    data = {
        "name": name,
        "targets": [{"email": email} for email in emails]
    }

    return gophish_request("POST", "groups/", data)


# -----------------------------------------------
# Create Landing Page
# -----------------------------------------------
@router.post("/landing")
def create_landing_page(name: str, html: str):
    data = {
        "name": name,
        "html": html
    }

    return gophish_request("POST", "pages/", data)


# -----------------------------------------------
# Launch Phishing Campaign
# -----------------------------------------------
@router.post("/campaign")
def launch_campaign(name: str, template_id: int, group_id: int, url: str, launch_date: str = None):
    data = {
        "name": name,
        "template": {"id": template_id},
        "groups": [{"id": group_id}],
        "url": url,
        "launch_date": launch_date  # Optional scheduling
    }

    return gophish_request("POST", "campaigns/", data)


# -----------------------------------------------
# Get All Campaigns
# -----------------------------------------------
@router.get("/campaigns")
def get_campaigns():
    return gophish_request("GET", "campaigns/")


# -----------------------------------------------
# Get Results of Campaign
# -----------------------------------------------
@router.get("/campaign/{campaign_id}/results")
def get_campaign_results(campaign_id: int):
    return gophish_request("GET", f"campaigns/{campaign_id}")
