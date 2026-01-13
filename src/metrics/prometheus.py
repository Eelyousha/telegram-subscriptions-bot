"""Prometheus metrics."""
from prometheus_client import Counter, Gauge, Histogram

# Business metrics
subscriptions_total = Gauge(
    "subscriptions_total",
    "Total number of active subscriptions",
)

subscriptions_monthly_amount_rub = Gauge(
    "subscriptions_monthly_amount_rub",
    "Total monthly subscription amount in RUB",
)

users_total = Gauge(
    "users_total",
    "Total number of users",
)

# Technical metrics
bot_commands_total = Counter(
    "bot_commands_total",
    "Total number of bot commands processed",
    ["command", "status"],
)

bot_command_duration_seconds = Histogram(
    "bot_command_duration_seconds",
    "Bot command processing duration",
    ["command"],
)

bot_active_users_24h = Gauge(
    "bot_active_users_24h",
    "Active users in last 24 hours",
)

db_operations_total = Counter(
    "db_operations_total",
    "Total database operations",
    ["operation", "status"],
)

notifications_sent_total = Counter(
    "notifications_sent_total",
    "Total notifications sent",
    ["status"],
)
