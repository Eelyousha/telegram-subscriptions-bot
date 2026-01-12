"""Database repositories."""
from src.db.repositories.subscription_analytics import SubscriptionAnalyticsRepository
from src.db.repositories.subscription_crud import SubscriptionCRUDRepository
from src.db.repositories.user_repository import UserRepository

# Maintain backward compatibility
SubscriptionRepository = SubscriptionCRUDRepository

__all__ = [
    "UserRepository",
    "SubscriptionCRUDRepository",
    "SubscriptionAnalyticsRepository",
    "SubscriptionRepository",  # For backward compatibility
]
