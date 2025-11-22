from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from datetime import datetime
from supabase import create_client

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

class StartRequest(BaseModel):
    employee_id: str
    training_id: str

@router.post("/start-training")
def start_training(req: StartRequest):
    # Check if record exists
    existing = supabase.table("training_progress").select("*") \
        .eq("employee_id", req.employee_id) \
        .eq("training_id", req.training_id) \
        .execute()

    if existing.data:
        # Update to in_progress
        prog_id = existing.data[0]["id"]
        supabase.table("training_progress").update({
            "status": "in_progress"
        }).eq("id", prog_id).execute()
    else:
        # Create new
        supabase.table("training_progress").insert({
            "employee_id": req.employee_id,
            "training_id": req.training_id,
            "status": "in_progress"
        }).execute()

    return {"message": "Training started"}

class CompleteRequest(BaseModel):
    employee_id: str
    training_id: str
    score: int | None = None

@router.post("/complete-training")
def complete_training(req: CompleteRequest):
    supabase.table("training_progress").update({
        "status": "completed",
        "score": req.score,
        "completed_at": datetime.utcnow().isoformat()
    }).eq("employee_id", req.employee_id).eq("training_id", req.training_id).execute()

    return {"message": "Training completed"}
