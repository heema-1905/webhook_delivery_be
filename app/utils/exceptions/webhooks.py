from dataclasses import dataclass


@dataclass
class WebhookEventException(Exception):
    """
    Exception raised for webhook events invalid flow.
    """

    message: str
    error: str

    def __str__(self):
        return f"{self.message}: {self.error}"
