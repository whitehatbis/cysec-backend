from fastapi import APIRouter, Query
import os
from supabase import create_client

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


@router.get("/dashboard/summary")
def dashboard_summary(org_id: str = Query(...)):

    # Get employees
    employees = supabase.table("employees") \
        .select("*") \
        .eq("org_id", org_id) \
        .execute()

    users = employees.data or []
    total_users = len(users)

    # 🔥 REAL LOGIC (no fake %)
    # For now:
    compliant_users = 0
    pending_training = total_users
    failed_phishing = 0
    awareness_score = 0

    # Optional: basic awareness logic
    if total_users > 0:
        awareness_score = int((compliant_users / total_users) * 100)

    return {
        "total_users": total_users,
        "compliant_users": compliant_users,
        "pending_training": pending_training,
        "failed_phishing": failed_phishing,
        "awareness_score": awareness_score
    }
