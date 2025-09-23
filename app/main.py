from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables from AWS SSM first
from .aws_ssm import set_env
set_env()

# Fallback to .env for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded .env file for local development")
except ImportError:
    print("python-dotenv not installed, skipping .env file")

from app.database import engine
from app.models import Base
from app.routers import auth, profile, images, events, public_events
import os

# Application configuration (hardcoded non-sensitive settings)
PROJECT_NAME = "Echoo API"
PROJECT_VERSION = "1.0.0" 
API_V1_STR = "/api/v1"
PORT = 8000
HOST = "0.0.0.0"

app = FastAPI(
    title=PROJECT_NAME,
    description="FastAPI backend for Echoo with event management, authentication, and FotoOwl integration",
    version=PROJECT_VERSION
)

# CORS configuration - allow all origins for dev environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://app.echoo.ing"],  # Allow all origins
    allow_credentials=True,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router, prefix=API_V1_STR, tags=["authentication"])
app.include_router(profile.router, prefix=API_V1_STR, tags=["profile"])
app.include_router(images.router, prefix=API_V1_STR, tags=["images"])
app.include_router(events.router, prefix=API_V1_STR, tags=["events"])
app.include_router(public_events.router, prefix=API_V1_STR, tags=["public-events"])

@app.get("/")
async def root():
    return {"message": f"{PROJECT_NAME} is running", "version": PROJECT_VERSION}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "environment": os.getenv("ENVIRONMENT", "development"),
        "service": "echoo-api"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    # Log the error (in production, you might want to send to a logging service)
    print(f"Unhandled error: {exc}")
    
    # Return error response to client
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "service": "echoo-api"}
    )