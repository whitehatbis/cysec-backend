from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from supabase import create_client

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

class OrganizationRequest(BaseModel):
    org_name: str
    admin_email: str

# ✅ CREATE ORGANIZATION
@router.post("/organizations")
def create_organization(req: OrganizationRequest):
    org = supabase.table("organizations").insert({
        "name": req.org_name
    }).execute()

    if not org.data:
        raise HTTPException(status_code=500, detail="Failed to create organization")

    org_id = org.data[0]["id"]

    admin = supabase.table("org_admins").insert({
        "org_id": org_id,
        "email": req.admin_email,
        "role": "admin",
        "status": "active"
    }).execute()

    return {"message": "Organization created successfully", "org_id": org_id}

# ✅ LIST ALL ORGANIZATIONS
@router.get("/organizations")
def list_organizations():
    orgs = supabase.table("organizations").select("*").execute()
    return orgs.data

# ✅ GET SINGLE ORG + STATUS
@router.get("/organizations/{org_id}")
def get_organization(org_id: str):
    org = supabase.table("organizations").select("*").eq("id", org_id).execute()
    if not org.data:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org.data[0]

# ✅ DISABLE ORG + USERS
@router.post("/organizations/{org_id}/disable")
def disable_organization(org_id: str):
    # Update org status
    supabase.table("organizations").update({"status": "inactive"}).eq("id", org_id).execute()
    # Update employees
    supabase.table("employees").update({"status": "inactive"}).eq("org_id", org_id).execute()
    # Update admins
    supabase.table("org_admins").update({"status": "inactive"}).eq("org_id", org_id).execute()

    return {"message": "Organization disabled successfully"}

# ✅ ENABLE ORG + USERS
@router.post("/organizations/{org_id}/enable")
def enable_organization(org_id: str):
    supabase.table("organizations").update({"status": "active"}).eq("id", org_id).execute()
    supabase.table("employees").update({"status": "active"}).eq("org_id", org_id).execute()
    supabase.table("org_admins").update({"status": "active"}).eq("org_id", org_id).execute()

    return {"message": "Organization enabled successfully"}
