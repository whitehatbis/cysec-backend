from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from supabase import create_client

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

class AssignmentRequest(BaseModel):
    org_id: str
    training_id: str
    assigned_by: str  # admin id

@router.post("/assign-training")
def assign_training(req: AssignmentRequest):
    assignment = supabase.table("training_assignments").insert({
        "org_id": req.org_id,
        "training_id": req.training_id,
        "assigned_by": req.assigned_by
    }).execute()

    if not assignment.data:
        raise HTTPException(status_code=500, detail="Failed to assign training")

    return {
        "message": "Training assigned successfully",
        "assignment_id": assignment.data[0]["id"]
    }
