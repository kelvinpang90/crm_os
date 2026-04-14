from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.middleware.logging import AccessLogMiddleware
from app.routers import auth, contacts, dashboard, users, tasks, pipeline, routing, webhooks, messages, analytics, sales_targets


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verify DB connection
    async with engine.connect() as conn:
        await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    # Start email poller
    from app.tasks.email_poller import start_email_poller, stop_email_poller
    start_email_poller()
    yield
    # Shutdown
    stop_email_poller()
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
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["漏斗"])
app.include_router(routing.router, prefix="/api/routing/rules", tags=["分配规则"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(messages.router, prefix="/api/messages", tags=["消息"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["数据分析"])
app.include_router(sales_targets.router, prefix="/api/sales-targets", tags=["销售目标"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "CRM API"}
