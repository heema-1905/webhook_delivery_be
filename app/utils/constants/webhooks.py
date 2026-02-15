from typing import List

from app.config.settings import settings

# Webhook delivery tasks config
MAX_RETRY_ATTEMPTS: int = 5
EXPONENTIAL_BACKOFF: List[int] = [1, 2, 4, 8, 16]

DOWNSTREAM_URL = f"{settings.BE_BASE_URL}/api/v1/webhooks/downstream/receive"

TASK_LOCKED_SECONDS = 30
DELIVERY_TIMEOUT = 3
