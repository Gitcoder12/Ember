from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(
    title="Ember",
    description="Heat-aware intelligence for food delivery.",
    version="0.1.0",
)

app.include_router(router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ember"}
