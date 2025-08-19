from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import model_validator


class Settings(BaseSettings):
    """
    This class holds in the key settings of the application; they are read from the .env file.
    Attribute names are self-descriptive, therefore no additional introduction is required.

    Following fields are required:
        - `DB_URI`
        - `DB_NAME`

    Moreover, the `NON_BLOCKING_AVAILABLE` has a default value of False; if it is True, the following fields are required:
        - `MQ_URL`
        - `QUEUE_NAME`
    """

    # Following fields are always required
    DB_ADDRESS: str
    DB_NAME: str
    NON_BLOCKING_AVAILABLE: bool = False

    # Optional unless NON_BLOCKING_AVAILABLE is true
    MQ_URL: Optional[str] = None
    QUEUE_NAME: Optional[str] = None

    # additional fields
    app_name: str = "Logging Microservice"
    app_version: str = "0.1.0"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    debug: bool = True
    allowed_keys: list[str]

    # model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @model_validator(mode="after")
    def check_non_blocking(cls, model):
        if model.NON_BLOCKING_AVAILABLE:
            missing = [
                field
                for field in (
                    "MQ_URL",
                    "QUEUE_NAME",
                )
                if getattr(model, field) in (None, "")
            ]
            if missing:
                raise ValueError(
                    "NON_BLOCKING_AVAILABLE is True, but these settings are missing: "
                    + ", ".join(missing)
                )
        return model


settings = Settings()
