from fastapi import FastAPI
from app.routers.organizations import router as org_router

app = FastAPI()

@app.get("/")
def root():
    return {"message": "CySec Backend is running!"}

app.include_router(org_router)
