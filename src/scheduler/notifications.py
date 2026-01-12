"""Notification scheduler."""
import asyncio
from datetime import date

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core.config import settings
from src.core.logging import get_logger
from src.db.database import AsyncSessionLocal
from src.db.repositories import SubscriptionRepository
from src.metrics.prometheus import notifications_sent_total

logger = get_logger(__name__)


async def send_notifications() -> None:
    """Send payment notifications to users."""
    logger.info("notification_task_started")

    bot = Bot(token=settings.bot_token)

    try:
        async with AsyncSessionLocal() as session:
            repo = SubscriptionRepository(session)
            today = date.today()
            subscriptions = await repo.get_pending_notifications(today)

            logger.info(
                "notifications_to_send",
                count=len(subscriptions),
                date=today.isoformat(),
            )

            for sub in subscriptions:
                days_left = (sub.next_payment - today).days
                text = (
                    f"🔔 Напоминание о подписке\n\n"
                    f"{sub.name} — {sub.amount} {sub.currency}\n"
                    f"Списание через {days_left} дн. ({sub.next_payment.strftime('%d.%m.%Y')})"
                )

                try:
                    await bot.send_message(chat_id=sub.telegram_id, text=text)
                    notifications_sent_total.labels(status="success").inc()
                    logger.info(
                        "notification_sent",
                        user_id=sub.telegram_id,
                        subscription_id=sub.id,
                    )
                except Exception as e:
                    notifications_sent_total.labels(status="error").inc()
                    logger.error(
                        "notification_failed",
                        user_id=sub.telegram_id,
                        subscription_id=sub.id,
                        error=str(e),
                    )

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)

    finally:
        await bot.session.close()

    logger.info("notification_task_completed")


async def advance_payments() -> None:
    """Advance past payment dates to next period."""
    logger.info("advance_payments_started")

    async with AsyncSessionLocal() as session:
        repo = SubscriptionRepository(session)
        count = await repo.advance_past_payments()

        logger.info("advance_payments_completed", advanced_count=count)


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure scheduler."""
    scheduler = AsyncIOScheduler()

    # Send notifications daily at configured hour
    scheduler.add_job(
        send_notifications,
        "cron",
        hour=settings.notification_hour,
        minute=0,
        id="send_notifications",
    )

    # Advance payments one hour after notifications
    scheduler.add_job(
        advance_payments,
        "cron",
        hour=settings.notification_hour + 1,
        minute=0,
        id="advance_payments",
    )

    logger.info(
        "scheduler_configured",
        notification_hour=settings.notification_hour,
    )

    return scheduler
