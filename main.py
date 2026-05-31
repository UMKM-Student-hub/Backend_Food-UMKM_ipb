from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from app.api.router import api_router
from app.core.exceptions import NotFoundError, BusinessRuleViolationError, PermissionDeniedError

load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "UniBites API"),
    version=os.getenv("APP_VERSION", "1.0.0")
)

os.makedirs("static/uploads/payments", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Selamat datang di UniBites API!", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

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

raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
allowed_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)