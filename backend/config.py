from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://nava:nava_dev@localhost:5432/nava"
    ANTHROPIC_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = ""
    OPENAI_API_KEY: str = ""
    GMAIL_CREDENTIALS_JSON: str = ""
    GMAIL_USER_EMAIL: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
