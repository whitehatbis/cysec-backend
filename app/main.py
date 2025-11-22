from fastapi import FastAPI
from app.routers.organizations import router as org_router
from app.routers.employees import router as emp_router
from app.routers.assignments import router as assign_router
from app.routers.trainings import router as training_router
from app.routers.progress import router as progress_router



app = FastAPI()

@app.get("/")
def root():
    return {"message": "CySec Backend is running!"}

app.include_router(org_router)
app.include_router(emp_router)
app.include_router(assign_router)
app.include_router(training_router)
app.include_router(progress_router)
