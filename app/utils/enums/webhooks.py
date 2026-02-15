from enum import Enum


class WebhookStatusEnum(str, Enum):
    """Enum class defining wbehook event statuses"""

    RECEIVED = "received"
    FAILED_TEMPORARILY = "failed_temporarily"
    FAILED_PERMANENTLY = "failed_permanently"
    DELIVERED = "delivered"
