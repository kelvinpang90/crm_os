from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.middleware.logging import AccessLogMiddleware
from app.routers import auth, contacts, dashboard, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB connection
    async with engine.connect() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(title="CRM API", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Access logging
app.add_middleware(AccessLogMiddleware)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["客户"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["仪表盘"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "CRM API"}
