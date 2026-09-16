import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router


def create_app() -> FastAPI:
    origins = ["http://localhost:5173"]
    if frontend_origin := os.getenv("FRONTEND_ORIGIN", "").strip().rstrip("/"):
        if frontend_origin not in origins:
            origins.append(frontend_origin)

    application = FastAPI(title="DispatchDiff", version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    application.include_router(router)
    return application


app = create_app()
