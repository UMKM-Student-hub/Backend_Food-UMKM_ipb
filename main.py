from fastapi import FastAPI
import os
from dotenv import load_dotenv
from app.api.router import api_router
from app.core.exceptions import NotFoundError, BusinessRuleViolationError, PermissionDeniedError
from fastapi.responses import JSONResponse
from fastapi import Request

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "UniBites API"),
    version=os.getenv("APP_VERSION", "1.0.0")
)

@app.get("/")
async def root():
    return {"message": "Selamat datang di UniBites API!", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "database_connection": "pending setup alembic"}

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(BusinessRuleViolationError)
async def business_rule_handler(request: Request, exc: BusinessRuleViolationError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(PermissionDeniedError)
async def permission_handler(request: Request, exc: PermissionDeniedError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})

app.include_router(api_router)