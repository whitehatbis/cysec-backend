from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from supabase import create_client

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)

class EmployeeRequest(BaseModel):
    org_id: str
    name: str
    email: str
    department: str | None = None

@router.post("/employees")
def add_employee(req: EmployeeRequest):
    emp = supabase.table("employees").insert({
        "org_id": req.org_id,
        "name": req.name,
        "email": req.email,
        "department": req.department
    }).execute()

    if not emp.data:
        raise HTTPException(status_code=500, detail="Failed to add employee")

    return {
        "message": "Employee added successfully",
        "employee_id": emp.data[0]["id"]
    }
