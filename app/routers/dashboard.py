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
        .select("id,email") \
        .eq("org_id", org_id) \
        .execute()

    users = employees.data or []
    total_users = len(users)

    employee_ids = [u["id"] for u in users]
    employee_emails = [u.get("email") for u in users if u.get("email")]

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
    failed_users = set()

    if employee_emails:
        phishing = supabase.table("phishing_events") \
            .select("recipient_email, event_type") \
            .in_("recipient_email", employee_emails) \
            .execute()

        phishing_data = phishing.data or []

        failed_users = set(
            p["recipient_email"] for p in phishing_data
            if p.get("event_type") == "click"
        )
    else:
        phishing_data = []

    failed_phishing = len(failed_users)

    # =============================
    # AWARENESS SCORE
    # =============================
    if total_users == 0:
        awareness_score = 0

    elif len(phishing_data) == 0:
        # No phishing data yet → neutral score
        awareness_score = 50

    else:
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
