from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    AGENT_MODE: str = "offline"
    GOOGLE_API_KEY: str | None = None
    LLM_PROVIDER: str = "gemini"
    MODEL_NAME: str = "gemini-2.5-flash-lite"
    TAVILY_API_KEY: str | None = None
    DATA_REFRESH_FREQ: str = "weekly"

    class Config:
        env_file = ".env"


settings = Settings()
