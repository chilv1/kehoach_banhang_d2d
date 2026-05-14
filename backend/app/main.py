"""FastAPI entry point — ProjectWeb (MS Project clone)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import Base, engine
from app import models  # noqa: F401
from app.routers import advanced, auth, projects
from app.sales_planner import models as sales_models  # noqa: F401
from app.sales_planner.routers import (
    ai_router, dashboard_router, exports_router, imports_router,
    map_router, sales_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api", tags=["projects"])
app.include_router(advanced.router, prefix="/api", tags=["advanced"])
app.include_router(auth.router, prefix="/api", tags=["auth"])

# Sales Campaign Planner module
app.include_router(imports_router, prefix="/api")
app.include_router(sales_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(map_router, prefix="/api")
app.include_router(exports_router, prefix="/api")


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
