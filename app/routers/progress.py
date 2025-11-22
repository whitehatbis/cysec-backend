from fastapi import APIRouter, HTTPException
import os
from supabase import create_client

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

@router.get("/employee-trainings")
def get_employee_trainings(employee_id: str):
    # 1️⃣ Get employee record
    emp = supabase.table("employees").select("*").eq("id", employee_id).execute()

    if not emp.data:
        raise HTTPException(status_code=404, detail="Employee not found")

    org_id = emp.data[0]["org_id"]

    # 2️⃣ Get trainings assigned to this org
    assignments = supabase.table("training_assignments").select("*").eq("org_id", org_id).execute()

    if not assignments.data:
        return []

    training_ids = [a["training_id"] for a in assignments.data]

    # 3️⃣ Fetch training details
    trainings = supabase.table("trainings").select("*").in_("id", training_ids).execute()

    # 4️⃣ Fetch progress (optional, default is not_started)
    progress = supabase.table("training_progress").select("*").eq("employee_id", employee_id).execute()

    progress_map = {p["training_id"]: p for p in progress.data}

    # 5️⃣ Build response
    result = []
    for t in trainings.data:
        tid = t["id"]
        status = "not_started"
        score = None

        if tid in progress_map:
            status = progress_map[tid]["status"]
            score = progress_map[tid]["score"]

        result.append({
            "training_id": tid,
            "title": t["title"],
            "description": t["description"],
            "status": status,
            "score": score
        })

    return result
