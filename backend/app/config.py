from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str

    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_OAUTH_REDIRECT_URI: str
    GITHUB_WEBHOOK_SECRET: str

    SLACK_WEBHOOK_URL: str
    SLACK_SIGNING_SECRET: str = ""

    ENCRYPTION_KEY: str
    SESSION_SECRET: str

    BACKEND_PUBLIC_URL: str
    FRONTEND_URL: str

    ENVIRONMENT: str = "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


settings = Settings()
