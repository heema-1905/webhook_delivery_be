from dataclasses import dataclass


@dataclass
class AuthenticationException(Exception):
    """
    Exception raised for user authentication invalid flow.
    """

    message: str
    error: str

    def __str__(self):
        return f"{self.message}: {self.error}"


@dataclass
class UtilsException(Exception):
    """
    Exception raised for common utils.
    """

    message: str
    error: str

    def __str__(self):
        return f"{self.message}: {self.error}"
