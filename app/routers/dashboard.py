from fastapi import APIRouter, Query
import os
from supabase import create_client

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


@router.get("/dashboard/summary")
def dashboard_summary(org_id: str = Query(...)):

    # =============================
    # TOTAL USERS
    # =============================
    employees = supabase.table("employees") \
        .select("id") \
        .eq("org_id", org_id) \
        .execute()

    users = employees.data or []
    total_users = len(users)

    employee_ids = [u["id"] for u in users]

    # =============================
    # TRAINING DATA
    # =============================
    progress = supabase.table("training_progress") \
        .select("employee_id, status") \
        .in_("employee_id", employee_ids) \
        .execute()

    progress_data = progress.data or []

    completed_users = set(
        p["employee_id"] for p in progress_data
        if p["status"] == "completed"
    )

    compliant_users = len(completed_users)
    pending_training = total_users - compliant_users

    # =============================
    # PHISHING DATA
    # =============================
    phishing = supabase.table("phishing_events") \
        .select("employee_id, gophish_event_type") \
        .in_("employee_id", employee_ids) \
        .execute()

    phishing_data = phishing.data or []

    failed_users = set(
        p["employee_id"] for p in phishing_data
        if p["gophish_event_type"] == "Clicked Link"
    )

    failed_phishing = len(failed_users)

    # =============================
    # AWARENESS SCORE
    # =============================
    awareness_score = 0
    if total_users > 0:
        safe_users = total_users - failed_phishing
        awareness_score = int((safe_users / total_users) * 100)

    # =============================
    # RESPONSE
    # =============================
    return {
        "total_users": total_users,
        "compliant_users": compliant_users,
        "pending_training": pending_training,
        "failed_phishing": failed_phishing,
        "awareness_score": awareness_score
    }
