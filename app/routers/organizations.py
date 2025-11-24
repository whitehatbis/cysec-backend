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


# ✅ 1️⃣ Create Organization + Admin
@router.post("/organizations")
def create_organization(req: OrganizationRequest):
    # Create organization
    org = supabase.table("organizations").insert({
        "name": req.org_name,
        "status": "active"
    }).execute()

    if not org.data:
        raise HTTPException(status_code=500, detail="Failed to create organization")

    org_id = org.data[0]["id"]

    # Create admin
    admin = supabase.table("org_admins").insert({
        "org_id": org_id,
        "email": req.admin_email,
        "role": "admin"
    }).execute()

    if not admin.data:
        raise HTTPException(status_code=500, detail="Failed to create admin")

    return {
        "message": "Organization created successfully",
        "org_id": org_id
    }


# ✅ 2️⃣ Disable Organization (Suspend Access)
@router.patch("/organizations/{org_id}/disable")
def disable_organization(org_id: str):
    result = supabase.table("organizations").update({
        "status": "inactive"
    }).eq("id", org_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {"message": "Organization disabled successfully"}


# ✅ 3️⃣ Enable Organization (Restore Access)
@router.patch("/organizations/{org_id}/enable")
def enable_organization(org_id: str):
    result = supabase.table("organizations").update({
        "status": "active"
    }).eq("id", org_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {"message": "Organization enabled successfully"}
