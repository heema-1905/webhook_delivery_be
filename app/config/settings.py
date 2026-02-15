from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.dtos.core import CorsAllowedSettingsDTO


class Settings(BaseSettings):
    """
    Settings class inheriting from BaseSettings class of pydantic-settings used for defining the
    .env config variables, default or static values and other configurable attributes required by the system
    """

    model_config = SettingsConfigDict(env_file=".env")

    # Debug settings
    DEBUG: bool

    # CORS Settings
    ALLOWED_ORIGINS: str
    ALLOWED_HEADERS: str
    ALLOWED_METHODS: str

    # FastAPI Settings
    APP_NAME: str
    APP_DESCRIPTION: str
    APP_VERSION: str

    # Database credentials
    MONGO_URL: str
    MONGO_DB_NAME: str

    # HMAC auth settings
    SECRET_KEY: str
    TIMESTAMP_TOLERANCE_SECONDS: int

    # Redis configurations
    REDIS_HOST: str
    REDIS_PORT: int

    # URL configurations
    BE_BASE_URL: str

    # Concurrency config
    CONCURRENT_WORKERS: int

    # Pagination settings
    PAGE_SIZE: int
    DEFAULT_PAGE: int

    @property
    def get_cors_allowed_settings(self) -> CorsAllowedSettingsDTO:
        """
        Return CORS settings as a structured DTO.

        Parses ALLOWED_ORIGINS, ALLOWED_HEADERS, and ALLOWED_METHODS.
        A wildcard "*" is returned as ["*"], otherwise values are split by commas.

        Returns:
            CorsAllowedSettingsDTO: Parsed CORS configuration.
        """

        def parse_cors_value(cors_value: str) -> List[str]:
            """
            Convert a CORS config string into a list of values.

            "*" → ["*"], else split by commas.
            """
            return ["*"] if "*" in cors_value else cors_value.split(",")

        return CorsAllowedSettingsDTO(
            allowed_origins=parse_cors_value(cors_value=self.ALLOWED_ORIGINS),
            allowed_headers=parse_cors_value(cors_value=self.ALLOWED_HEADERS),
            allowed_methods=parse_cors_value(cors_value=self.ALLOWED_HEADERS),
        )


settings: Settings = Settings()
