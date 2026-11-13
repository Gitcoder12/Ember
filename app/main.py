import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.core.middleware import RequestIdMiddleware
from app.services.heat_prediction import resolve_parameters

logger = logging.getLogger("ember")


def create_app() -> FastAPI:
    settings = get_settings()
    resolve_parameters(settings)  # fail fast on a missing or corrupt calibration file
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    application = FastAPI(
        title="Ember",
        description="Heat-aware intelligence for food delivery.",
        version="0.1.0",
    )
    application.add_middleware(RequestIdMiddleware)
    application.include_router(router, prefix="/api/v1")

    @application.exception_handler(Exception)
    async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("unhandled error request_id=%s", request_id)
        # Never leak exception details to clients; the request ID links to the server log.
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )
        if request_id:
            response.headers["X-Request-ID"] = request_id
        return response

    @application.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "ember"}

    return application


app = create_app()
