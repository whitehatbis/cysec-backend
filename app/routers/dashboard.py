from fastapi import APIRouter, Query
import os
from supabase import create_client

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


@router.get("/dashboard/summary")
def dashboard_summary(org_id: str = Query(...)):

    users = supabase.table("employees") \
        .select("*") \
        .eq("org_id", org_id) \
        .execute()

    total_users = len(users.data or [])

    # Temporary mock logic
    compliant_users = int(total_users * 0.6)
    pending_training = total_users - compliant_users
    failed_phishing = int(total_users * 0.3)
    awareness_score = 70

    return {
        "total_users": total_users,
        "compliant_users": compliant_users,
        "pending_training": pending_training,
        "failed_phishing": failed_phishing,
        "awareness_score": awareness_score
    }
