from fastapi import FastAPI
from app.routers.organizations import router as org_router
from app.routers.employees import router as emp_router
from app.routers.assignments import router as assign_router
from app.routers.trainings import router as training_router
from app.routers.progress import router as progress_router
from app.routers.training_progress import router as progress_update_router
from app.routers.google_sync import router as google_sync_router
from app.routers.phishing import router as phishing_router



app = FastAPI()

@app.get("/")
def root():
    return {"message": "CySec Backend is running!"}

app.include_router(org_router)
app.include_router(emp_router)
app.include_router(assign_router)
app.include_router(training_router)
app.include_router(progress_router)
app.include_router(progress_update_router)
app.include_router(google_sync_router)
app.include_router(phishing_router)
