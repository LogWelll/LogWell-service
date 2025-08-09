from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from settings import settings
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from database import init_db
from logs.routes import logging_router
from security.api_key_verifier import verify_api_key
import logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Optional: log startup event
    logging.info("🔌 Initializing DB connection...")
    await init_db(settings.DB_ADDRESS, settings.DB_NAME)

    yield  # app is running...

    # Optional: log shutdown event
    logging.info("🛑 Cleaning up on shutdown...")
    if hasattr(app.state, "listener"):
        app.state.listener.cancel()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url=settings.docs_url if settings.debug else None,
    redoc_url=settings.redoc_url if settings.debug else None,
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(logging_router, prefix="/logs", tags=["logs"], dependencies=[Depends(verify_api_key)])


@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Returns the index.html file
    """
    with open("templates/index.html", "r") as f:
        index_html = f.read()
    return index_html
