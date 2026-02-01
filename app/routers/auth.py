from fastapi import APIRouter, Header, HTTPException
from supabase import create_client
import os
import jwt

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


def get_email_from_token(auth_header: str):
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = auth_header.replace("Bearer ", "")
    decoded = jwt.decode(token, options={"verify_signature": False})
    return decoded.get("email")


@router.get("/me")
def get_me(Authorization: str = Header(None)):
    email = get_email_from_token(Authorization)

    # Check org_admins
    admin = supabase.table("org_admins").select("*").eq("email", email).execute()
    if admin.data:
        return {
            "role": "admin",
            "org_id": admin.data[0]["org_id"],
            "email": email
        }

    # Check employees
    emp = supabase.table("employees").select("*").eq("email", email).execute()
    if emp.data:
        return {
            "role": "employee",
            "org_id": emp.data[0]["org_id"],
            "email": email
        }

    raise HTTPException(status_code=403, detail="User not linked to any organization")
