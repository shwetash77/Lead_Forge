"""Settings read from environment variables (see .env.example)."""
import os


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./leadforge.db")
        # Shared secret the WordPress plugin sends in the X-API-Key header.
        # If empty, auth is disabled (fine for local development only).
        self.api_key = os.getenv("LEADFORGE_API_KEY", "")
        # LLM scoring. If no key is set, the rule-based fallback is used.
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.llm_model = os.getenv("LLM_MODEL", "claude-sonnet-5-5")
        self.llm_timeout = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))
        # CRM sync. If no token is set, sync is skipped.
        self.hubspot_token = os.getenv("HUBSPOT_TOKEN", "")


def get_settings() -> Settings:
    return Settings()
