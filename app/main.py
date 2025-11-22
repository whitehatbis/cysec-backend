from fastapi import FastAPI
from app.routers.organizations import router as org_router
from app.routers.employees import router as emp_router

app = FastAPI()

@app.get("/")
def root():
    return {"message": "CySec Backend is running!"}

app.include_router(org_router)
app.include_router(emp_router)
