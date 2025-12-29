import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.utils import build_vectorstore, load_docs

logger = logging.getLogger(__name__)

DATA_URLS = {
    "langgraph-llms.txt": "https://langchain-ai.github.io/langgraph/llms.txt",
    "langgraph-llms-full.txt": "https://langchain-ai.github.io/langgraph/llms-full.txt",
    "langchain-llms.txt": "https://docs.langchain.com/llms.txt",
    "langchain-llms-full.txt": "https://docs.langchain.com/llms-full.txt",
}

DATA_PATHS = [
    "data/langgraph-llms.txt",
    "data/langgraph-llms-full.txt",
    "data/langchain-llms.txt",
    "data/langchain-llms-full.txt",
]


class DataRefresher:
    """Automated data refresh scheduler."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self._schedule_jobs()

    def _download_docs(self) -> bool:
        """Download fresh docs."""
        logger.info("🚀 Starting data refresh...")
        try:
            for filename, url in DATA_URLS.items():
                filepath = Path("data") / filename
                logger.info(f"Downloading {filename}...")

                response = requests.get(url, timeout=30)
                response.raise_for_status()

                Path("data").mkdir(exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(response.text)

                logger.info(f"✅ Downloaded {filename} ({len(response.text)} chars)")

            last_update = datetime.now().isoformat()
            with open("data/last_update.txt", "w") as f:
                f.write(last_update)
            logger.info(f"Data last updated: {last_update}")
            return True

        except Exception as e:
            logger.error(f"Download failed: {e}")
            return False

    async def _rebuild_vectorstore(self):
        """Rebuild Chroma index."""
        try:
            logger.info("Rebuilding vectorstore...")
            shutil.rmtree("vectorstore/chroma", ignore_errors=True)

            docs = load_docs(DATA_PATHS)
            if docs:
                build_vectorstore(docs)
                logger.info(f"Vectorstore rebuilt with {len(docs)} chunks")
            else:
                logger.warning("No docs to rebuild")

        except Exception as e:
            logger.error(f"Vectorstore rebuild failed: {e}")

    async def refresh_all(self):
        """Full refresh: download + rebuild."""
        success = self._download_docs()
        if success:
            await self._rebuild_vectorstore()
            logger.info("Data refresh completed!")
        else:
            logger.error("Data refresh failed")

    def _schedule_jobs(self):
        """Schedule weekly/monthly jobs."""
        refresh_freq = os.getenv("DATA_REFRESH_FREQ", "weekly")
        if refresh_freq == "weekly":
            self.scheduler.add_job(
                self.refresh_all,
                "cron",
                hour=2,
                minute=0,
                day_of_week="sun",
                id="weekly_refresh",
                replace_existing=True,
            )
        else:
            self.scheduler.add_job(
                self.refresh_all,
                "cron",
                hour=2,
                minute=0,
                day=1,
                id="monthly_refresh",
                replace_existing=True,
            )

        logger.info(f"Scheduled {refresh_freq} data refresh")

    async def start(self):
        """Start scheduler."""
        self.scheduler.start()
        logger.info("Data refresher started")

    async def shutdown(self):
        """Stop scheduler."""
        self.scheduler.shutdown()
        logger.info("Data refresher stopped")
