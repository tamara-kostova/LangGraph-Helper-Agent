import logging

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from api.routes import router as chat_router
from app.agent import HelperAgent
from app.data_refresh import DataRefresher
from config import settings

logging.basicConfig(level=logging.INFO)


logger = logging.getLogger(__name__)
data_refresher: DataRefresher = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global data_refresher
    logger.info(f"Starting FastAPI with AGENT_MODE={settings.AGENT_MODE}")
    app.state.helper_agent = HelperAgent()
    data_refresher = DataRefresher()
    await data_refresher.start()

    yield

    logger.info("FastAPI shutting down...")
    if data_refresher:
        await data_refresher.shutdown()


app = FastAPI(title="LangGraph Helper Agent", lifespan=lifespan)


app.include_router(chat_router)


@app.get("/health")
async def health():
    return {"status": "healthy", "mode": settings.AGENT_MODE}


@app.post("/admin/refresh")
async def manual_refresh():
    """Manual data refresh endpoint."""
    if data_refresher:
        await data_refresher.refresh_all()
        return {"status": "refresh_completed"}
    return {"status": "refresher_not_running"}
