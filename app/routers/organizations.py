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

@router.post("/organizations")
def create_organization(req: OrganizationRequest):
    # 1️⃣ Insert organization
    org = supabase.table("organizations").insert({
        "name": req.org_name
    }).execute()

    if not org.data:
        raise HTTPException(status_code=500, detail="Failed to create organization")

    org_id = org.data[0]["id"]

    # 2️⃣ Insert admin
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
