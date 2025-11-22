from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from supabase import create_client

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

class TrainingRequest(BaseModel):
    title: str
    description: str | None = None
    content_url: str | None = None

@router.post("/trainings")
def create_training(req: TrainingRequest):
    training = supabase.table("trainings").insert({
        "title": req.title,
        "description": req.description,
        "content_url": req.content_url
    }).execute()

    if not training.data:
        raise HTTPException(status_code=500, detail="Failed to create training")

    return {
        "message": "Training created successfully",
        "training_id": training.data[0]["id"]
    }
