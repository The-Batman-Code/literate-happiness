"""Production-grade configuration management using Pydantic."""

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Google ADK Settings
    google_api_key: SecretStr = Field(
        ...,
        description="Google API key for Gemini model",
    )
    google_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model to use for agents",
    )
    google_use_vertexai: bool = Field(
        default=False,
        description="Use Vertex AI backend instead of Google AI Studio",
    )
    google_cloud_project: str | None = Field(
        default=None,
        description="GCP project ID (required if using Vertex AI)",
    )
    google_cloud_location: str = Field(
        default="us-central1",
        description="GCP location for Vertex AI services",
    )

    # LinkedIn Agent Settings
    linkedin_cookie: str | None = Field(
        default=None,
        description="LinkedIn session cookie for MCP server authentication",
    )

    # Adzuna API Settings
    adzuna_app_id: SecretStr | None = Field(
        default=None,
        description="Adzuna API application ID",
    )
    adzuna_app_key: SecretStr | None = Field(
        default=None,
        description="Adzuna API application key",
    )

    # Application Settings
    environment: str = Field(
        default="development",
        description="Environment: development, staging, production",
    )
    app_name: str = Field(
        default="job-researcher",
        description="Application name for logging and identification",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode (development only)",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value is one of allowed values."""
        valid_environments = {"development", "staging", "production"}
        if v.lower() not in valid_environments:
            msg = f"Environment must be one of {valid_environments}, got: {v}"
            raise ValueError(msg)
        return v.lower()

    def validate_production(self) -> None:
        """Additional validation for production environment."""
        if self.environment == "production":
            if not self.google_api_key.get_secret_value():
                msg = "GOOGLE_API_KEY is required in production"
                raise ValueError(msg)

            if self.google_use_vertexai and not self.google_cloud_project:
                msg = "GOOGLE_CLOUD_PROJECT is required when using Vertex AI"
                raise ValueError(msg)

    def __str__(self) -> str:
        """String representation that hides secrets."""
        linkedin_status = "set" if self.linkedin_cookie else "not set"
        return (
            "Settings("
            f"environment={self.environment}, "
            f"app_name={self.app_name}, "
            f"debug={self.debug}, "
            "google_api_key=***MASKED***, "
            f"google_use_vertexai={self.google_use_vertexai}, "
            f"linkedin_cookie={linkedin_status}"
            ")"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get application settings (cached with LRU)."""
    settings = Settings()  # type: ignore[call-arg]

    if settings.environment == "production":
        settings.validate_production()

    return settings


__all__ = [
    "Settings",
    "get_settings",
]
