
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.materials import router as materials_router
from app.api.v1.suppliers import router as suppliers_router
from app.api.v1.batches import router as batches_router
from app.api.v1.recipes import router as recipes_router
from app.api.v1.production_jobs import router as production_jobs_router
from app.api.v1.ai import router as ai_router


from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(materials_router, prefix="/api/v1")
app.include_router(suppliers_router, prefix="/api/v1")
app.include_router(batches_router, prefix="/api/v1")
app.include_router(
    recipes_router,
    prefix="/api/v1/recipes",
    tags=["Recipes"],
)
app.include_router(ai_router, prefix="/api/v1/ai", tags=["AI Assistant"])
app.include_router(
    production_jobs_router,
    prefix="/api/v1/production-jobs",
    tags=["Production Jobs"],
)



@app.get("/")
async def root():
    return {
        "message": "Welcome to CandleFlow AI",
        "version": settings.APP_VERSION,
    }
