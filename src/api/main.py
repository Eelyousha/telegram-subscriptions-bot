"""FastAPI application entry point."""
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.api.routes import health, subscriptions, users
from src.core.config import settings
from src.core.logging import configure_logging, get_logger
from src.db.database import AsyncSessionLocal
from src.db.repositories import SubscriptionRepository, UserRepository
from src.metrics.prometheus import (
    bot_active_users_24h,
    subscriptions_monthly_amount_rub,
    subscriptions_total,
    users_total,
)
from src.scheduler.notifications import create_scheduler

logger = get_logger(__name__)


async def update_metrics() -> None:
    """Update Prometheus metrics."""
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        sub_repo = SubscriptionRepository(session)

        users_total.set(await user_repo.count_total())
        bot_active_users_24h.set(await user_repo.count_active_24h())
        subscriptions_total.set(await sub_repo.count_total())
        subscriptions_monthly_amount_rub.set(
            await sub_repo.get_total_monthly_amount_rub()
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    configure_logging()
    logger.info("api_starting", host=settings.api_host, port=settings.api_port)

    # Start scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("scheduler_started")

    # Start metrics update task
    async def metrics_updater():
        while True:
            try:
                await update_metrics()
            except Exception as e:
                logger.error("metrics_update_failed", error=str(e))
            await asyncio.sleep(60)  # Update every minute

    metrics_task = asyncio.create_task(metrics_updater())

    yield

    # Shutdown
    logger.info("api_shutting_down")
    scheduler.shutdown()
    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Subscription Tracker API",
    description="API for tracking subscriptions",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(users.router)
app.include_router(subscriptions.router)
app.include_router(health.router)


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_config=None,  # Use our own logging
    )
