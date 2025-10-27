from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import uvicorn
import logging

from app.database import get_db, engine
from app.models import Base
from app.routers import auth, users, contacts, campaigns, templates, messages, dashboard, admin, billing, reports, webhooks, two_way_sms, automation, ab_testing, survey
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables with error handling
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create database tables: {e}")
    logger.info("Continuing without database - using mock data")

app = FastAPI(
    title="SMS Marketing Platform API",
    description="Professional SMS marketing and bulk messaging platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
app.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
app.include_router(templates.router, prefix="/templates", tags=["templates"])
app.include_router(messages.router, prefix="/messages", tags=["messages"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(billing.router, prefix="/billing", tags=["billing"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(two_way_sms.router, prefix="/two-way-sms", tags=["two-way-sms"])
app.include_router(automation.router, prefix="/automation", tags=["automation"])
app.include_router(ab_testing.router, prefix="/ab-testing", tags=["ab-testing"])
app.include_router(survey.router, prefix="/surveys", tags=["surveys"])

@app.get("/")
async def root():
    return {"message": "SMS Marketing Platform API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
